# Cargar variables de entorno primero
import load_env

import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_mail import Mail, Message
import sqlite3
from datetime import datetime, timedelta
import pytz
LIMA_TZ = pytz.timezone('America/Lima')
from kasa import SmartPlug
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from functools import lru_cache
from authlib.integrations.flask_client import OAuth
import secrets

# Configuración de logging profesional
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))

# Configuración adicional para sesiones
is_production = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_SECURE'] = is_production  # True en HTTPS (producción)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hora

# Configuración específica para producción
if is_production:
    app.config['PREFERRED_URL_SCHEME'] = 'https'

# Configuración de correo electrónico
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# Inicializar Flask-Mail
mail = Mail(app)

# Configuración OAuth Google
oauth = OAuth(app)

# Configuración de Google OAuth
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', 'tu_google_client_id_aqui')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', 'tu_google_client_secret_aqui')

# Verificar si las credenciales de Google están configuradas
GOOGLE_OAUTH_ENABLED = GOOGLE_CLIENT_ID != 'tu_google_client_id_aqui' and GOOGLE_CLIENT_SECRET != 'tu_google_client_secret_aqui'

if GOOGLE_OAUTH_ENABLED:
    try:
        # Configuración manual robusta sin dependencia de metadata
        google = oauth.register(
            name='google',
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
            access_token_url='https://oauth2.googleapis.com/token',
            refresh_token_url='https://oauth2.googleapis.com/token',
            client_kwargs={
                'scope': 'openid email profile'
            },
        )
        logging.info("Google OAuth configurado correctamente (configuración manual robusta)")
    except Exception as e:
        logging.error(f"Error configurando Google OAuth: {e}")
        GOOGLE_OAUTH_ENABLED = False
        google = None
else:
    google = None
    logging.warning("Google OAuth no configurado - usando credenciales por defecto")

# Configuración de la base de datos
DB_PATH = 'ener_virgil.db'

# Cache en memoria para optimización
_cache = {}
_cache_lock = threading.Lock()
CACHE_TIMEOUT = 300  # 5 minutos

# Pool de threads para operaciones asíncronas
executor = ThreadPoolExecutor(max_workers=4)

def get_cache(key):
    """Obtiene un valor del cache si no ha expirado"""
    with _cache_lock:
        if key in _cache:
            value, timestamp = _cache[key]
            if time.time() - timestamp < CACHE_TIMEOUT:
                return value
            else:
                del _cache[key]
    return None

def set_cache(key, value):
    """Guarda un valor en el cache"""
    with _cache_lock:
        _cache[key] = (value, time.time())

def clear_cache_pattern(pattern):
    """Limpia entradas del cache que coincidan con un patrón"""
    with _cache_lock:
        keys_to_delete = [k for k in _cache.keys() if pattern in k]
        for key in keys_to_delete:
            del _cache[key]

# Utilidades centralizadas

def safe_check_password_hash(pwhash, password):
    """
    Función segura para verificar contraseñas que maneja diferentes tipos de hash
    """
    try:
        # Intenta usar el método estándar de Werkzeug
        return check_password_hash(pwhash, password)
    except ValueError as e:
        if "unsupported hash type" in str(e):
            # Si el hash no es soportado, intenta con métodos alternativos
            logging.warning(f"Hash no soportado: {e}. Intentando métodos alternativos.")
            
            # Si es un hash scrypt, intenta recrear el usuario con un hash compatible
            if pwhash.startswith('scrypt:'):
                logging.info("Detectado hash scrypt no compatible. Se requiere recrear la contraseña.")
                return False
            
            # Para otros tipos de hash no soportados
            return False
        else:
            # Re-lanza la excepción si es un error diferente
            raise e
    except Exception as e:
        logging.error(f"Error inesperado al verificar contraseña: {e}")
        return False

def safe_generate_password_hash(password):
    """
    Genera un hash de contraseña usando un método compatible
    """
    try:
        # Usa pbkdf2:sha256 que es más compatible
        return generate_password_hash(password, method='pbkdf2:sha256')
    except Exception as e:
        logging.error(f"Error al generar hash: {e}")
        # Fallback a un método simple (solo para desarrollo)
        return generate_password_hash(password)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")  # Mejora el rendimiento
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=10000")
    return conn

@lru_cache(maxsize=128)
def get_user_by_receipt(receipt_number):
    cache_key = f"user_receipt_{receipt_number}"
    cached = get_cache(cache_key)
    if cached:
        return cached
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE receipt_number = ?", (receipt_number,))
    user = c.fetchone()
    conn.close()
    
    if user:
        set_cache(cache_key, user)
    return user

@lru_cache(maxsize=128)
def get_user_by_username(username):
    cache_key = f"user_username_{username}"
    cached = get_cache(cache_key)
    if cached:
        return cached
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    
    if user:
        set_cache(cache_key, user)
    return user

def get_devices_by_user(user_id):
    cache_key = f"devices_user_{user_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, ip_address FROM devices WHERE user_id = ?", (user_id,))
    devices = c.fetchall()
    conn.close()
    
    set_cache(cache_key, devices)
    return devices

def get_user_by_google_id(google_id):
    """Obtiene usuario por Google ID"""
    cache_key = f"user_google_{google_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE google_id = ?", (google_id,))
    user = c.fetchone()
    conn.close()
    
    if user:
        set_cache(cache_key, user)
    return user

def get_user_by_email(email):
    """Obtiene usuario por email"""
    cache_key = f"user_email_{email}"
    cached = get_cache(cache_key)
    if cached:
        return cached
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()
    
    if user:
        set_cache(cache_key, user)
    return user

def create_google_user(google_id, email, name, picture_url):
    """Crea un nuevo usuario desde Google OAuth"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Generar username único basado en email
        username = email.split('@')[0] if email else f"user_{google_id}"
        counter = 1
        original_username = username
        
        # Verificar si el username ya existe
        while True:
            c.execute("SELECT id FROM users WHERE username = ?", (username,))
            if not c.fetchone():
                break
            username = f"{original_username}{counter}"
            counter += 1
        
        # Preparar valores seguros
        safe_name = name if name else username
        safe_picture = picture_url if picture_url else None
        current_time = datetime.now(LIMA_TZ)
        
        # Insertar usuario de Google con la nueva estructura
        c.execute("""INSERT INTO users 
                     (username, full_name, phone, dni, receipt_number, password, 
                      email, google_id, profile_picture, auth_method, created_at) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'google', ?)""",
                  (username, safe_name, None, None, None, '', 
                   email, google_id, safe_picture, current_time))
        
        user_id = c.lastrowid
        conn.commit()
        conn.close()
        
        logging.info(f"Usuario Google creado exitosamente: ID={user_id}, username={username}")
        
        # Limpiar cache relacionado
        clear_cache_pattern(f"user_google_{google_id}")
        clear_cache_pattern(f"user_email_{email}")
        
        return user_id
        
    except sqlite3.IntegrityError as e:
        logging.error(f"Error de integridad al crear usuario Google: {e}")
        if 'conn' in locals():
            conn.close()
        return None
    except Exception as e:
        logging.error(f"Error inesperado creando usuario Google: {e}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        if 'conn' in locals():
            conn.close()
        return None

def update_google_user_info(google_id, email, name, picture_url):
    """Actualiza información del usuario de Google"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Actualizar información del usuario de Google
        c.execute("""UPDATE users 
                     SET full_name = ?, email = ?, profile_picture = ? 
                     WHERE google_id = ?""",
                  (name or '', email or '', picture_url, google_id))
        
        rows_affected = c.rowcount
        conn.commit()
        conn.close()
        
        logging.info(f"Usuario Google actualizado: {rows_affected} filas afectadas")
        
        # Limpiar cache
        clear_cache_pattern(f"user_google_{google_id}")
        clear_cache_pattern(f"user_email_{email}")
        
        return rows_affected > 0
        
    except Exception as e:
        logging.error(f"Error actualizando usuario Google: {e}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        if 'conn' in locals():
            conn.close()
        return False

def save_consumption(user_id, device_id, consumption_kwh):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT INTO consumption (user_id, device_id, consumption_kwh, timestamp) VALUES (?, ?, ?, ?)",
                  (user_id, device_id, consumption_kwh, datetime.now()))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error guardando consumo: {e}")

# Funciones de correo electrónico

def verificar_configuracion_correo():
    """Verifica si la configuración de correo está completa"""
    required_configs = ['MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER']
    for config in required_configs:
        if not app.config.get(config) or app.config.get(config) in ['tu_email@gmail.com', 'tu_app_password_aqui']:
            return False
    return True

def obtener_estadisticas_usuario(user_id):
    """Obtiene estadísticas reales del usuario para personalizar el correo"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Obtener fecha de registro
        c.execute("SELECT created_at FROM users WHERE id = ?", (user_id,))
        created_at = c.fetchone()
        dias_activo = 1
        
        if created_at and created_at[0]:
            try:
                fecha_registro = datetime.fromisoformat(created_at[0].replace('Z', '+00:00'))
                dias_activo = max(1, (datetime.now(LIMA_TZ) - fecha_registro.replace(tzinfo=LIMA_TZ)).days)
            except:
                dias_activo = 1
        
        # Contar dispositivos conectados
        c.execute("SELECT COUNT(*) FROM devices WHERE user_id = ?", (user_id,))
        dispositivos_conectados = c.fetchone()[0] or 0
        
        # Calcular consumo total del último mes
        fecha_inicio = datetime.now(LIMA_TZ) - timedelta(days=30)
        c.execute("""SELECT SUM(consumption_kwh) FROM consumption 
                     WHERE user_id = ? AND timestamp >= ?""", 
                  (user_id, fecha_inicio))
        consumo_mes = c.fetchone()[0] or 0
        
        # Estimar ahorro (basado en consumo vs promedio)
        ahorro_estimado = min(35, max(5, int(25 + (dispositivos_conectados * 3))))
        
        # Estimar CO2 reducido (aproximadamente 0.5 kg CO2 por kWh ahorrado)
        co2_reducido = max(1, int(consumo_mes * 0.5 * (ahorro_estimado / 100)))
        
        conn.close()
        
        return {
            'dias_activo': dias_activo,
            'dispositivos_conectados': dispositivos_conectados,
            'ahorro_estimado': ahorro_estimado,
            'co2_reducido': co2_reducido,
            'consumo_mes': round(consumo_mes, 2)
        }
        
    except Exception as e:
        logging.error(f"Error obteniendo estadísticas de usuario: {e}")
        # Valores por defecto en caso de error
        return {
            'dias_activo': 1,
            'dispositivos_conectados': 0,
            'ahorro_estimado': 15,
            'co2_reducido': 5,
            'consumo_mes': 0
        }

def enviar_correo_bienvenida(email, nombre, es_nuevo_usuario=True, user_id=None):
    """Envía correo de bienvenida a usuarios de Google OAuth usando templates HTML mejorados"""
    try:
        # Verificar configuración de correo
        if not verificar_configuracion_correo():
            logging.warning("Configuración de correo incompleta. No se enviará correo de bienvenida.")
            return False
        
        # Determinar el tipo de mensaje
        if es_nuevo_usuario:
            asunto = "¡Bienvenido a EnerVirgil! 🌱⚡ Tu viaje hacia el ahorro energético comienza aquí"
            tipo_mensaje = "registro"
            template_name = "email_bienvenida.html"
        else:
            asunto = "¡Bienvenido de vuelta a EnerVirgil! 🌱⚡ Continuemos ahorrando energía"
            tipo_mensaje = "login"
            template_name = "email_bienvenida_vuelta.html"
        
        # Crear mensaje
        msg = Message(
            subject=asunto,
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[email]
        )
        
        # Obtener estadísticas reales del usuario si está disponible
        if user_id:
            stats = obtener_estadisticas_usuario(user_id)
        else:
            # Valores por defecto para nuevos usuarios
            stats = {
                'dias_activo': 1,
                'dispositivos_conectados': 0,
                'ahorro_estimado': 20,
                'co2_reducido': 5,
                'consumo_mes': 0
            }
        
        # Preparar datos para el template
        template_data = {
            'nombre': nombre,
            'fecha_actual': datetime.now(LIMA_TZ).strftime('%d de %B de %Y'),
            'fecha_login': datetime.now(LIMA_TZ).strftime('%d/%m/%Y a las %H:%M'),
            'dias_activo': stats['dias_activo'],
            'dispositivos_conectados': stats['dispositivos_conectados'],
            'ahorro_estimado': stats['ahorro_estimado'],
            'co2_reducido': stats['co2_reducido'],
            'consumo_mes': stats.get('consumo_mes', 0),
            'base_url': os.environ.get('BASE_URL', 'http://localhost:5000')
        }
        
        # Renderizar el template HTML
        try:
            msg.html = render_template(template_name, **template_data)
        except Exception as template_error:
            logging.error(f"Error renderizando template {template_name}: {template_error}")
            # Fallback a HTML básico si el template falla
            msg.html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 30px; text-align: center; border-radius: 10px;">
                    <h1>🌱 {'¡Bienvenido a EnerVirgil!' if es_nuevo_usuario else '¡Bienvenido de vuelta!'} ⚡</h1>
                    <p>Tu asistente inteligente para el ahorro energético</p>
                </div>
                <div style="background: #f8fffe; padding: 30px; border-radius: 10px; margin-top: 20px;">
                    <h2>¡Hola {nombre}!</h2>
                    <p>{'Nos emociona tenerte en EnerVirgil! Has dado el primer paso hacia un futuro más sostenible.' if es_nuevo_usuario else 'Nos alegra verte de vuelta en EnerVirgil. Continuemos optimizando tu consumo energético.'}</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{os.environ.get('BASE_URL', 'http://localhost:5000')}" style="background: #10b981; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold;">
                            {'Comenzar Ahora' if es_nuevo_usuario else 'Ir al Dashboard'}
                        </a>
                    </div>
                </div>
                <div style="text-align: center; margin-top: 20px; color: #666; font-size: 14px;">
                    <p>EnerVirgil - Tu aliado en el ahorro energético</p>
                </div>
            </div>
            """
        
        # Enviar correo en background para no bloquear la aplicación
        def enviar_async():
            try:
                with app.app_context():
                    mail.send(msg)
                logging.info(f"Correo de {tipo_mensaje} enviado exitosamente a {email}")
                return True
            except Exception as e:
                logging.error(f"Error enviando correo a {email}: {e}")
                return False
        
        # Ejecutar en background
        executor.submit(enviar_async)
        return True
        
    except Exception as e:
        logging.error(f"Error preparando correo de bienvenida: {e}")
        return False

def enviar_correo_test(email_destino):
    """Envía un correo de prueba para verificar la configuración"""
    try:
        if not verificar_configuracion_correo():
            return False, "Configuración de correo incompleta"
        
        msg = Message(
            subject="🧪 Correo de Prueba - EnerVirgil",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[email_destino]
        )
        
        msg.html = """
        <h2>🧪 Correo de Prueba</h2>
        <p>Si recibes este correo, la configuración de email está funcionando correctamente.</p>
        <p><strong>EnerVirgil</strong> - Sistema de monitoreo energético</p>
        """
        
        mail.send(msg)
        return True, "Correo de prueba enviado exitosamente"
        
    except Exception as e:
        return False, f"Error enviando correo de prueba: {e}"

# Inicialización de la base de datos

def check_column_exists(cursor, table_name, column_name):
    """Verifica si una columna existe en una tabla"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in cursor.fetchall()]
    return column_name in columns

def migrate_database():
    """Migra la base de datos existente para agregar nuevas columnas"""
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # Verificar y agregar nuevas columnas a la tabla users
        new_columns = [
            ('google_id', 'TEXT UNIQUE'),
            ('email', 'TEXT'),
            ('profile_picture', 'TEXT'),
            ('auth_method', 'TEXT DEFAULT "local"'),
            ('created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP')
        ]
        
        for column_name, column_type in new_columns:
            if not check_column_exists(c, 'users', column_name):
                try:
                    c.execute(f'ALTER TABLE users ADD COLUMN {column_name} {column_type}')
                    logging.info(f"Columna {column_name} agregada a la tabla users")
                except sqlite3.OperationalError as e:
                    logging.warning(f"Error agregando columna {column_name}: {e}")
        
        # Hacer que phone, dni y receipt_number sean opcionales para usuarios existentes
        # (SQLite no permite modificar columnas, pero los datos existentes seguirán funcionando)
        
        conn.commit()
        logging.info("Migración de base de datos completada")
        
    except Exception as e:
        logging.error(f"Error durante la migración: {e}")
        conn.rollback()
    finally:
        conn.close()

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Crear tablas básicas primero
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT NOT NULL UNIQUE,
                  full_name TEXT NOT NULL,
                  phone TEXT NOT NULL,
                  dni TEXT NOT NULL UNIQUE,
                  receipt_number TEXT NOT NULL UNIQUE,
                  password TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS consumption
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  device_id INTEGER,
                  consumption_kwh REAL,
                  timestamp DATETIME,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS devices
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  name TEXT NOT NULL,
                  ip_address TEXT NOT NULL UNIQUE,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()
    
    # Ejecutar migración para agregar nuevas columnas
    migrate_database()
    
    # Crear índices después de la migración
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # Crear índices básicos
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_receipt ON users(receipt_number)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_devices_user ON devices(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_devices_ip ON devices(ip_address)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_consumption_user ON consumption(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_consumption_device ON consumption(device_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_consumption_timestamp ON consumption(timestamp)')
        
        # Crear índices para nuevas columnas (solo si existen)
        if check_column_exists(c, 'users', 'google_id'):
            c.execute('CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id)')
        if check_column_exists(c, 'users', 'email'):
            c.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        
        conn.commit()
        logging.info("Índices creados exitosamente")
        
    except Exception as e:
        logging.error(f"Error creando índices: {e}")
    finally:
        conn.close()

init_db()

COST_PER_KWH = 0.50  # En PEN

# Obtener datos de consumo energético real desde TP-Link Tapo P110 (optimizado)
async def get_real_energy_data(device_id, ip_address, user_id=None, timeout=3):
    cache_key = f"energy_data_{device_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached
    
    try:
        plug = SmartPlug(ip_address)
        # Timeout más corto para evitar bloqueos
        await asyncio.wait_for(plug.update(), timeout=timeout)
        consumption_watts = plug.emeter_realtime.get("power", 0)
        consumption_kwh = consumption_watts / 1000
        status = plug.is_on
        
        result = {
            "id": device_id,
            "name": "Enchufe Tapo P110",
            "consumption": round(consumption_kwh, 2),
            "status": status,
            "ip_address": ip_address
        }
        
        # Cache por 30 segundos para datos en tiempo real
        with _cache_lock:
            _cache[cache_key] = (result, time.time())
        
        # Guardar consumo en background
        if user_id is not None:
            executor.submit(save_consumption, user_id, device_id, consumption_kwh)
        
        return result
    except asyncio.TimeoutError:
        logging.warning(f"Timeout al obtener datos del enchufe (IP: {ip_address})")
        return {
            "id": device_id,
            "name": "Enchufe Tapo P110",
            "consumption": 0.0,
            "status": False,
            "ip_address": ip_address,
            "error": "timeout"
        }
    except Exception as e:
        logging.error(f"Error al obtener datos del enchufe (IP: {ip_address}): {e}")
        return {
            "id": device_id,
            "name": "Enchufe Tapo P110",
            "consumption": 0.0,
            "status": False,
            "ip_address": ip_address,
            "error": str(e)
        }

def get_energy_data(receipt_number):
    cache_key = f"energy_data_user_{receipt_number}"
    cached = get_cache(cache_key)
    if cached:
        return cached
    
    devices = []
    try:
        user = get_user_by_receipt(receipt_number)
        if user:
            user_id = user[0]
            device_records = get_devices_by_user(user_id)
            if device_records:
                async def gather_devices():
                    # Timeout global más corto
                    tasks = [get_real_energy_data(device_id, ip_address, user_id, timeout=2) 
                            for device_id, name, ip_address in device_records]
                    return await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=10)
                
                try:
                    devices = asyncio.run(gather_devices())
                    # Filtrar excepciones
                    devices = [d for d in devices if not isinstance(d, Exception)]
                except asyncio.TimeoutError:
                    logging.warning("Timeout global al obtener datos de dispositivos")
                    # Devolver datos básicos sin consumo en tiempo real
                    devices = [{
                        "id": device_id,
                        "name": name,
                        "consumption": 0.0,
                        "status": False,
                        "ip_address": ip_address,
                        "error": "timeout"
                    } for device_id, name, ip_address in device_records]
    except Exception as e:
        logging.error(f"Error al obtener dispositivos: {e}")
    
    # Cache por 30 segundos
    with _cache_lock:
        _cache[cache_key] = (devices, time.time())
    
    return devices

def get_recommendations(total_consumption, devices, receipt_number):
    recommendations = []
    avg_consumption = 1.5
    user_factor = int(receipt_number[-2:]) / 100 if receipt_number and receipt_number[-2:].isdigit() else 1.0
    if total_consumption > avg_consumption * len(devices) * 1.2:
        savings = round(total_consumption * 0.15 * COST_PER_KWH, 2)
        recommendations.append({
            "text": f"Tu consumo total ({total_consumption:.2f} kWh) es alto. Reduce el uso durante horas pico (6-10 PM) para ahorrar {savings} PEN/mes.",
            "category": "Consumo General",
            "priority": "Alta"
        })
    for device in devices:
        if not device["status"] and device["consumption"] > 0.05:
            savings = round(device["consumption"] * 0.05 * COST_PER_KWH, 2)
            recommendations.append({
                "text": f"El {device['name']} está en standby consumiendo {device['consumption']:.2f} kWh. Desconéctalo para ahorrar {savings} PEN/mes.",
                "category": "Consumo en Standby",
                "priority": "Baja"
            })
    if user_factor > 1.0:
        recommendations.append({
            "text": f"Tu perfil de consumo es {user_factor*100:.0f}% superior al promedio. Revisa el uso de dispositivos grandes como aires acondicionados o calentadores.",
            "category": "Perfil de Usuario",
            "priority": "Alta"
        })
    if not recommendations:
        recommendations.append({
            "text": "Tu consumo está dentro de lo normal. Mantén buenas prácticas como apagar luces innecesarias.",
            "category": "General",
            "priority": "Baja"
        })
    return recommendations

import requests
import re

GOOGLE_API_KEY = 'AIzaSyDswCwJtL0fMsWNc3U8vqRRzqz7dhSr-rI'
GOOGLE_CX = 'b427110346f954ba1'

# Base de datos local de consumos típicos (kWh/día)
CONSUMOS_TIPICOS = {
    # Electrodomésticos grandes
    'refrigerador': 1.5, 'refrigeradora': 1.5, 'nevera': 1.5, 'frigorífico': 1.5,
    'aire acondicionado': 8.0, 'ac': 8.0, 'climatizador': 6.0,
    'lavadora': 0.8, 'lavarropas': 0.8,
    'secadora': 3.0, 'secador de ropa': 3.0,
    'lavavajillas': 1.2, 'lavaplatos': 1.2,
    'horno': 2.4, 'horno eléctrico': 2.4,
    'microondas': 0.4, 'micro ondas': 0.4,
    
    # Calefacción y agua
    'calentador de agua': 4.0, 'terma': 4.0, 'boiler': 4.0,
    'calefactor': 2.0, 'estufa eléctrica': 2.0,
    'radiador': 1.5,
    
    # Entretenimiento
    'televisor': 0.3, 'tv': 0.3, 'televisión': 0.3,
    'computadora': 0.4, 'pc': 0.4, 'ordenador': 0.4,
    'laptop': 0.1, 'portátil': 0.1,
    'consola': 0.2, 'playstation': 0.2, 'xbox': 0.2,
    
    # Iluminación
    'bombilla led': 0.024, 'foco led': 0.024, 'lámpara led': 0.024,
    'bombilla': 0.144, 'foco': 0.144, 'lámpara': 0.144,
    'fluorescente': 0.096,
    
    # Pequeños electrodomésticos
    'ventilador': 0.2, 'abanico': 0.2,
    'plancha': 0.3, 'ferro': 0.3,
    'aspiradora': 0.4, 'aspirador': 0.4,
    'licuadora': 0.1, 'batidora': 0.1,
    'tostadora': 0.2, 'tostador': 0.2,
    'cafetera': 0.2,
    'hervidor': 0.3, 'pava eléctrica': 0.3,
    
    # Otros
    'cargador': 0.024, 'cargador celular': 0.024,
    'router': 0.048, 'modem': 0.048,
    'impresora': 0.1,
    'monitor': 0.2, 'pantalla': 0.2,
}

def obtener_consumo_local(nombre_dispositivo):
    """
    Busca el consumo en la base de datos local
    """
    nombre_lower = nombre_dispositivo.lower().strip()
    
    # Búsqueda exacta
    if nombre_lower in CONSUMOS_TIPICOS:
        return CONSUMOS_TIPICOS[nombre_lower]
    
    # Búsqueda por palabras clave
    for dispositivo, consumo in CONSUMOS_TIPICOS.items():
        if dispositivo in nombre_lower or nombre_lower in dispositivo:
            return consumo
    
    # Búsqueda por palabras parciales
    palabras_dispositivo = nombre_lower.split()
    for palabra in palabras_dispositivo:
        if len(palabra) > 3:  # Solo palabras significativas
            for dispositivo, consumo in CONSUMOS_TIPICOS.items():
                if palabra in dispositivo:
                    return consumo
    
    return None

def obtener_consumo_completo(nombre_dispositivo):
    """
    Obtiene el consumo usando cache, base local y Google API como último recurso
    """
    cache_key = f"consumo_completo_{nombre_dispositivo.lower()}"
    cached = get_cache(cache_key)
    if cached:
        return cached
    
    # Primero intentar base de datos local (más rápido)
    consumo_local = obtener_consumo_local(nombre_dispositivo)
    if consumo_local is not None:
        result = (consumo_local, "Base de datos local")
        set_cache(cache_key, result)
        return result
    
    # Solo usar Google API si no hay datos locales y en background
    def fetch_google_async():
        try:
            consumo_google = obtener_consumo_google(nombre_dispositivo)
            if consumo_google is not None:
                result = (consumo_google, "Google API")
                set_cache(cache_key, result)
                return result
        except Exception as e:
            logging.error(f"Error en Google API: {e}")
        return None, "No encontrado"
    
    # Ejecutar en background para no bloquear
    future = executor.submit(fetch_google_async)
    try:
        # Timeout muy corto para Google API
        result = future.result(timeout=2)
        return result
    except:
        # Si Google falla o es lento, devolver sin datos
        return None, "No encontrado"

def obtener_consumo_google(nombre_dispositivo):
    """
    Busca patrones de consumo (optimizado con timeout corto)
    """
    cache_key = f"google_consumo_{nombre_dispositivo.lower()}"
    cached = get_cache(cache_key)
    if cached:
        return cached
    
    import re
    query = f"{nombre_dispositivo} consumo eléctrico kWh watts potencia"
    url = (
        f"https://www.googleapis.com/customsearch/v1"
        f"?key={GOOGLE_API_KEY}&cx={GOOGLE_CX}&q={query}"
    )
    
    try:
        # Timeout muy corto
        resp = requests.get(url, timeout=3)
        
        if resp.status_code != 200:
            return None
            
        data = resp.json()
        
        for item in data.get('items', [])[:3]:  # Solo los primeros 3 resultados
            snippet = item.get('snippet', '')
            title = item.get('title', '')
            full_text = f"{title} {snippet}".lower()
            
            # Patrones optimizados (solo los más comunes)
            patterns = [
                (r'(\d+[.,]?\d*)\s*kwh\s*/?(?:por\s*)?d[ií]a', 1),
                (r'(\d+[.,]?\d*)\s*kwh\s*/?(?:por\s*)?mes', 1/30),
                (r'(\d+[.,]?\d*)\s*w(?:atts?)?\b', 24/1000),
                (r'(\d+[.,]?\d*)\s*kw\b', 24),
            ]
            
            for pattern, multiplier in patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    value = float(match.group(1).replace(',', '.'))
                    result = round(value * multiplier, 3)
                    set_cache(cache_key, result)
                    return result
        
        return None
        
    except Exception as e:
        logging.error(f"Error consultando Google: {e}")
        return None

def obtener_fragmentos_google(nombre_dispositivo):
    """
    Obtiene fragmentos (optimizado para ser asíncrono)
    """
    cache_key = f"google_fragmentos_{nombre_dispositivo.lower()}"
    cached = get_cache(cache_key)
    if cached:
        return cached
    
    # Ejecutar en background para no bloquear la página
    def fetch_fragments():
        try:
            query = f"{nombre_dispositivo} consumo eléctrico especificaciones"
            url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CX}&q={query}"
            
            resp = requests.get(url, timeout=3)
            if resp.status_code != 200:
                return []
                
            data = resp.json()
            fragmentos = []
            
            for item in data.get('items', [])[:3]:  # Solo 3 resultados
                snippet = item.get('snippet', '')
                title = item.get('title', '')
                
                if snippet and len(snippet.strip()) > 20:
                    full_snippet = f"<strong>{title}</strong><br>{snippet}" if title else snippet
                    fragmentos.append(full_snippet)
            
            set_cache(cache_key, fragmentos)
            return fragmentos
            
        except Exception as e:
            logging.error(f"Error obteniendo fragmentos: {e}")
            return []
    
    # Ejecutar en background
    future = executor.submit(fetch_fragments)
    try:
        return future.result(timeout=1)  # Timeout muy corto
    except:
        return []  # Si falla, devolver lista vacía

# Reglas de automatización
def check_automation_rules():
    # Esta función necesita ser llamada desde un contexto que tenga acceso a session
    # Por ahora, la dejamos como placeholder para evitar errores
    logging.info("Reglas de automatización ejecutadas")

def validate_registration_form(form):
    username = form.get('username', '').strip()
    full_name = form.get('full_name', '').strip()
    phone = form.get('phone', '').strip()
    dni = form.get('dni', '').strip()
    receipt_number = form.get('receipt_number', '').strip()
    password = form.get('password', '')
    if not dni.isdigit() or len(dni) != 8:
        return False, "El DNI debe contener exactamente 8 dígitos numéricos."
    if not receipt_number.isdigit() or not (6 <= len(receipt_number) <= 8):
        return False, "El número de recibo debe contener entre 6 y 8 dígitos numéricos."
    if not phone.isdigit():
        return False, "El número de teléfono debe contener solo números."
    if not username or not full_name or not password:
        return False, "Campos incompletos. Por favor, completa todos los campos."
    return True, ""

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        valid, error = validate_registration_form(request.form)
        if not valid:
            return render_template('register.html', error=error)
        username = request.form['username'].strip()
        full_name = request.form['full_name'].strip()
        phone = request.form['phone'].strip()
        dni = request.form['dni'].strip()
        receipt_number = request.form['receipt_number'].strip()
        password = request.form['password']
        hashed_password = safe_generate_password_hash(password)
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("INSERT INTO users (username, full_name, phone, dni, receipt_number, password) VALUES (?, ?, ?, ?, ?, ?)",
                      (username, full_name, phone, dni, receipt_number, hashed_password))
            conn.commit()
            conn.close()
            session['success_message'] = f"Usuario '{username}' creado con éxito"
            return redirect(url_for('login'))
        except sqlite3.IntegrityError as e:
            logging.warning(f"Error de integridad: {e}")
            return render_template('register.html', error="Usuario, DNI o número de recibo ya registrados.")
        except Exception as e:
            logging.error(f"Error inesperado: {e}")
            return render_template('register.html', error="Error al guardar el usuario. Intenta de nuevo.")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    success_message = session.pop('success_message', None)
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = get_user_by_username(username)
        if user:
            # Verificar si es usuario de Google (no tiene contraseña local)
            # Manejar casos donde auth_method puede no existir
            auth_method = user[10] if len(user) > 10 and user[10] else 'local'
            if auth_method == 'google':
                return render_template('login.html', error="Esta cuenta está vinculada con Google. Usa 'Iniciar con Google'.", google_enabled=GOOGLE_OAUTH_ENABLED)
            
            password_check_result = safe_check_password_hash(user[6], password)
            if password_check_result:
                session['user_id'] = user[0]
                session['username'] = username
                session['receipt_number'] = user[5] if user[5] else None
                session['auth_method'] = 'local'
                session['email'] = user[8] if len(user) > 8 and user[8] else None
                return redirect(url_for('dashboard'))
            else:
                # Verificar si es un problema de hash scrypt
                if user[6] and user[6].startswith('scrypt:'):
                    error_msg = ("Tu contraseña usa un formato incompatible. "
                               "Por favor, usa el enlace 'Restablecer contraseña' para solucionarlo.")
                else:
                    error_msg = "Contraseña incorrecta."
                return render_template('login.html', error=error_msg, google_enabled=GOOGLE_OAUTH_ENABLED)
        else:
            return render_template('login.html', error="Usuario no registrado.", google_enabled=GOOGLE_OAUTH_ENABLED)
    return render_template('login.html', success_message=success_message, google_enabled=GOOGLE_OAUTH_ENABLED)

@app.route('/auth/google')
def google_login():
    """Inicia el proceso de autenticación con Google"""
    if not GOOGLE_OAUTH_ENABLED or not google:
        return render_template('login.html', error="Google OAuth no está configurado. Contacta al administrador.")
    
    try:
        # Limpiar cualquier estado OAuth previo
        oauth_keys = ['oauth_nonce', 'oauth_state', '_google_authlib_state_', '_google_authlib_nonce_']
        for key in oauth_keys:
            session.pop(key, None)
        
        redirect_uri = url_for('google_callback', _external=True)
        logging.info(f"Redirect URI: {redirect_uri}")
        
        # Usar authorize_redirect sin nonce personalizado para evitar conflictos
        return google.authorize_redirect(redirect_uri)
    except Exception as e:
        logging.error(f"Error iniciando Google OAuth: {e}")
        return render_template('login.html', error="Error al conectar con Google. Intenta más tarde.")

@app.route('/auth/google/callback')
def google_callback():
    """Callback de Google OAuth - Versión ultra robusta con logging detallado"""
    if not GOOGLE_OAUTH_ENABLED or not google:
        logging.error("Google OAuth no está habilitado")
        return render_template('login.html', error="Google OAuth no está configurado.", google_enabled=GOOGLE_OAUTH_ENABLED)
    
    try:
        logging.info("=== INICIANDO CALLBACK DE GOOGLE OAUTH ===")
        logging.info(f"Request URL: {request.url}")
        logging.info(f"Request args: {dict(request.args)}")
        logging.info(f"Request method: {request.method}")
        logging.info(f"Request headers: {dict(request.headers)}")
        
        # Verificar si hay error en la respuesta de Google
        if 'error' in request.args:
            error = request.args.get('error')
            error_description = request.args.get('error_description', '')
            logging.error(f"Error de Google OAuth: {error} - {error_description}")
            
            # Mapear errores comunes
            if error == 'access_denied':
                error_msg = "Acceso denegado. El usuario canceló la autorización."
            elif error == 'invalid_request':
                error_msg = "Solicitud inválida. Verifica la configuración OAuth."
            else:
                error_msg = f"Error de Google: {error_description or error}"
            
            return render_template('login.html', error=error_msg, google_enabled=GOOGLE_OAUTH_ENABLED)
        
        # Verificar que tenemos el código de autorización
        code = request.args.get('code')
        if not code:
            logging.error("No se recibió código de autorización")
            return render_template('login.html', 
                error="No se recibió código de autorización de Google. Intenta nuevamente.", 
                google_enabled=GOOGLE_OAUTH_ENABLED)
        
        logging.info(f"Código de autorización recibido: {code[:20]}...")
        
        # Preparar datos para intercambio de token
        import requests
        
        token_url = 'https://oauth2.googleapis.com/token'
        redirect_uri = url_for('google_callback', _external=True)
        
        token_data = {
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }
        
        logging.info(f"Solicitando token a: {token_url}")
        logging.info(f"Redirect URI usado: {redirect_uri}")
        logging.info(f"Client ID usado: {GOOGLE_CLIENT_ID[:20]}...")
        
        # Obtener token con headers apropiados
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        try:
            response = requests.post(token_url, data=token_data, headers=headers, timeout=15)
            logging.info(f"Respuesta del token endpoint: {response.status_code}")
            logging.info(f"Headers de respuesta: {dict(response.headers)}")
            
            if response.status_code != 200:
                logging.error(f"Error obteniendo token: {response.status_code}")
                logging.error(f"Respuesta completa: {response.text}")
                
                # Intentar parsear el error
                try:
                    error_data = response.json()
                    error_description = error_data.get('error_description', 'Error desconocido')
                    logging.error(f"Error detallado: {error_description}")
                    return render_template('login.html', 
                        error=f"Error de Google OAuth: {error_description}", 
                        google_enabled=GOOGLE_OAUTH_ENABLED)
                except:
                    return render_template('login.html', 
                        error=f"Error al obtener token de Google (código {response.status_code}). Verifica la configuración.", 
                        google_enabled=GOOGLE_OAUTH_ENABLED)
            
            token = response.json()
            logging.info(f"Token obtenido exitosamente. Keys: {list(token.keys())}")
            
            if 'access_token' not in token:
                logging.error(f"Token inválido recibido: {token}")
                return render_template('login.html', 
                    error="Token de Google inválido. Intenta nuevamente.", 
                    google_enabled=GOOGLE_OAUTH_ENABLED)
            
        except requests.exceptions.Timeout:
            logging.error("Timeout al solicitar token")
            return render_template('login.html', 
                error="Timeout al conectar con Google. Intenta nuevamente.", 
                google_enabled=GOOGLE_OAUTH_ENABLED)
        except requests.exceptions.RequestException as e:
            logging.error(f"Error de conexión al solicitar token: {e}")
            return render_template('login.html', 
                error="Error de conexión con Google. Verifica tu internet.", 
                google_enabled=GOOGLE_OAUTH_ENABLED)
        
        # Obtener información del usuario
        userinfo_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        auth_headers = {
            'Authorization': f"Bearer {token['access_token']}",
            'Accept': 'application/json'
        }
        
        logging.info("Obteniendo información del usuario de Google")
        
        try:
            user_response = requests.get(userinfo_url, headers=auth_headers, timeout=15)
            logging.info(f"Respuesta del userinfo endpoint: {user_response.status_code}")
            
            if user_response.status_code != 200:
                logging.error(f"Error obteniendo userinfo: {user_response.status_code}")
                logging.error(f"Respuesta userinfo: {user_response.text}")
                return render_template('login.html', 
                    error="Error al obtener información del usuario de Google.", 
                    google_enabled=GOOGLE_OAUTH_ENABLED)
            
            user_info = user_response.json()
            logging.info(f"Información de usuario obtenida exitosamente")
            logging.info(f"User info keys: {list(user_info.keys())}")
            
        except requests.exceptions.Timeout:
            logging.error("Timeout al obtener userinfo")
            return render_template('login.html', 
                error="Timeout al obtener información de usuario. Intenta nuevamente.", 
                google_enabled=GOOGLE_OAUTH_ENABLED)
        except requests.exceptions.RequestException as e:
            logging.error(f"Error de conexión al obtener userinfo: {e}")
            return render_template('login.html', 
                error="Error de conexión al obtener información de usuario.", 
                google_enabled=GOOGLE_OAUTH_ENABLED)
        
        # Extraer y validar información del usuario
        google_id = user_info.get('id')
        email = user_info.get('email')
        name = user_info.get('name')
        picture = user_info.get('picture')
        
        logging.info(f"Datos extraídos - ID: {google_id}, Email: {email}, Name: {name}")
        
        if not google_id:
            logging.error("Google ID no encontrado en la respuesta")
            return render_template('login.html', 
                error="No se pudo obtener ID de Google. Intenta nuevamente.", 
                google_enabled=GOOGLE_OAUTH_ENABLED)
        
        if not email:
            logging.error("Email no encontrado en la respuesta")
            return render_template('login.html', 
                error="No se pudo obtener email de Google. Verifica los permisos.", 
                google_enabled=GOOGLE_OAUTH_ENABLED)
        
        # Buscar usuario existente por Google ID
        logging.info(f"Buscando usuario existente con Google ID: {google_id}")
        
        try:
            user = get_user_by_google_id(google_id)
            es_nuevo_usuario = False
            
            if user:
                logging.info("Usuario existente encontrado, actualizando información")
                # Usuario existente - actualizar información
                update_google_user_info(google_id, email, name, picture)
                user_id = user[0]
                username = user[1]
                receipt_number = user[5] if len(user) > 5 and user[5] else None
                es_nuevo_usuario = False
            else:
                logging.info("Usuario nuevo, verificando email existente")
                # Verificar si existe usuario con el mismo email
                existing_user = get_user_by_email(email)
                if existing_user:
                    auth_method = existing_user[10] if len(existing_user) > 10 and existing_user[10] else 'local'
                    if auth_method == 'local':
                        logging.warning(f"Email {email} ya existe como usuario local")
                        return render_template('login.html', 
                            error=f"Ya existe una cuenta local con el email {email}. Inicia sesión con usuario y contraseña.", 
                            google_enabled=GOOGLE_OAUTH_ENABLED)
                
                # Crear nuevo usuario
                logging.info("Creando nuevo usuario de Google")
                user_id = create_google_user(google_id, email, name, picture)
                if not user_id:
                    logging.error("Error al crear usuario de Google")
                    return render_template('login.html', 
                        error="Error al crear cuenta con Google. Intenta nuevamente.", 
                        google_enabled=GOOGLE_OAUTH_ENABLED)
                
                # Obtener datos del usuario recién creado
                user = get_user_by_google_id(google_id)
                if not user:
                    logging.error("No se pudo obtener usuario recién creado")
                    return render_template('login.html', 
                        error="Error interno al crear usuario. Intenta nuevamente.", 
                        google_enabled=GOOGLE_OAUTH_ENABLED)
                
                username = user[1]
                receipt_number = None
                es_nuevo_usuario = True
                logging.info(f"Usuario creado exitosamente: {username}")
            
            # Enviar correo de bienvenida
            logging.info(f"Enviando correo de bienvenida a {email} (nuevo usuario: {es_nuevo_usuario})")
            enviar_correo_bienvenida(email, name or username, es_nuevo_usuario, user_id)
        
        except Exception as db_error:
            logging.error(f"Error de base de datos: {db_error}")
            return render_template('login.html', 
                error="Error de base de datos. Intenta nuevamente.", 
                google_enabled=GOOGLE_OAUTH_ENABLED)
        
        # Limpiar cualquier estado OAuth residual
        oauth_keys = ['oauth_nonce', 'oauth_state', '_google_authlib_state_', '_google_authlib_nonce_']
        for key in oauth_keys:
            session.pop(key, None)
        
        # Establecer sesión
        logging.info("Estableciendo sesión de usuario")
        session.clear()  # Limpiar sesión anterior
        session['user_id'] = user_id
        session['username'] = username
        session['receipt_number'] = receipt_number
        session['auth_method'] = 'google'
        session['email'] = email
        session['profile_picture'] = picture
        session['google_id'] = google_id
        
        # Mensaje de bienvenida
        if not receipt_number:
            session['info_message'] = "¡Bienvenido! Para acceder a todas las funciones, completa tu perfil con tu número de recibo de luz."
        
        logging.info(f"=== LOGIN EXITOSO PARA USUARIO: {username} ===")
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        logging.error(f"Error crítico en Google callback: {type(e).__name__}: {str(e)}")
        import traceback
        logging.error(f"Traceback completo: {traceback.format_exc()}")
        
        # Limpiar sesión OAuth en caso de error
        oauth_keys = ['oauth_nonce', 'oauth_state', '_google_authlib_state_', '_google_authlib_nonce_']
        for key in oauth_keys:
            session.pop(key, None)
        
        return render_template('login.html', 
            error="Error interno durante la autenticación. Por favor, intenta nuevamente o contacta al soporte.", 
            google_enabled=GOOGLE_OAUTH_ENABLED)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Verificar si el usuario de Google necesita completar perfil
    if session.get('auth_method') == 'google' and not session.get('receipt_number'):
        info_message = session.pop('info_message', None)
        if info_message:
            session['info_message'] = info_message
    
    # Cargar datos básicos rápidamente
    receipt_number = session.get('receipt_number')
    
    # Si no hay receipt_number, mostrar dashboard limitado
    if not receipt_number:
        return render_template('dashboard.html', 
                             devices=[], 
                             total_consumption=0, 
                             total_cost=0, 
                             recommendations=[{
                                 "text": "Completa tu perfil con el número de recibo para acceder a todas las funciones de monitoreo.",
                                 "category": "Configuración",
                                 "priority": "Alta"
                             }], 
                             consumption_data={'daily': {'labels': [], 'data': []}, 'weekly': {'labels': [], 'data': []}, 'monthly': {'labels': [], 'data': []}},
                             show_complete_profile=True)
    
    # Usar cache para datos que no cambian frecuentemente
    cache_key = f"dashboard_{receipt_number}"
    cached_data = get_cache(cache_key)
    
    if cached_data:
        cached_data['show_complete_profile'] = False
        return render_template('dashboard.html', **cached_data)
    
    # Obtener datos en paralelo para mejorar rendimiento
    def get_dashboard_data():
        energy_data = get_energy_data(receipt_number)
        total_consumption = sum(device.get('consumption', 0) for device in energy_data)
        total_cost = total_consumption * COST_PER_KWH
        recommendations = get_recommendations(total_consumption, energy_data, receipt_number)
        consumption_data = generate_consumption_data(receipt_number)
        
        return {
            'devices': energy_data,
            'total_consumption': total_consumption,
            'total_cost': total_cost,
            'recommendations': recommendations,
            'consumption_data': consumption_data,
            'show_complete_profile': False
        }
    
    # Ejecutar en background si es necesario
    try:
        dashboard_data = get_dashboard_data()
        # Cache por 30 segundos
        with _cache_lock:
            _cache[cache_key] = (dashboard_data, time.time())
        return render_template('dashboard.html', **dashboard_data)
    except Exception as e:
        logging.error(f"Error en dashboard: {e}")
        # Datos de fallback
        return render_template('dashboard.html', 
                             devices=[], 
                             total_consumption=0, 
                             total_cost=0, 
                             recommendations=[], 
                             consumption_data={'daily': {'labels': [], 'data': []}, 'weekly': {'labels': [], 'data': []}, 'monthly': {'labels': [], 'data': []}},
                             show_complete_profile=False)

def generate_consumption_data(receipt_number):
    user = get_user_by_receipt(receipt_number)
    if not user:
        return {
            'daily': {'labels': [], 'data': []},
            'weekly': {'labels': [], 'data': []},
            'monthly': {'labels': [], 'data': []}
        }
    user_id = user[0]
    conn = get_db_connection()
    c = conn.cursor()
    current_date = datetime.now()
    daily_labels = [(current_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    daily_data = []
    for i in range(7):
        start_date = (current_date - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        c.execute("SELECT SUM(consumption_kwh) FROM consumption WHERE user_id = ? AND timestamp >= ? AND timestamp < ?",
                  (user_id, start_date, end_date))
        result = c.fetchone()[0]
        daily_data.append(round(result or 0, 2))
    weekly_labels = [f'Semana {i+1}' for i in range(4)]
    weekly_data = []
    for i in range(4):
        start_date = (current_date - timedelta(days=(i+1)*7)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=7)
        c.execute("SELECT SUM(consumption_kwh) FROM consumption WHERE user_id = ? AND timestamp >= ? AND timestamp < ?",
                  (user_id, start_date, end_date))
        result = c.fetchone()[0]
        weekly_data.append(round(result or 0, 2))
    monthly_labels = [(current_date - timedelta(days=i*30)).strftime('%Y-%m') for i in range(11, -1, -1)]
    monthly_data = []
    for i in range(12):
        start_date = (current_date - timedelta(days=(i+1)*30)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=30)
        c.execute("SELECT SUM(consumption_kwh) FROM consumption WHERE user_id = ? AND timestamp >= ? AND timestamp < ?",
                  (user_id, start_date, end_date))
        result = c.fetchone()[0]
        monthly_data.append(round(result or 0, 2))
    conn.close()
    return {
        'daily': {'labels': daily_labels, 'data': daily_data},
        'weekly': {'labels': weekly_labels, 'data': weekly_data},
        'monthly': {'labels': monthly_labels, 'data': monthly_data}
    }

@app.route('/detalles_dispositivos', methods=['GET'])
def detalles_dispositivos():
    """
    Muestra detalles de dispositivos (optimizado)
    """
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = get_user_by_receipt(session['receipt_number'])
    if not user:
        return render_template('detalles_dispositivos.html', devices=[], detalle=None, selected_device_id=None)
    
    user_id = user[0]
    selected_device_id = request.args.get('device_id', type=int)
    
    # Cache para lista de dispositivos
    cache_key = f"devices_list_{user_id}"
    devices = get_cache(cache_key)
    
    if not devices:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT id, name FROM devices WHERE user_id = ?", (user_id,))
        devices = [dict(id=row[0], name=row[1]) for row in c.fetchall()]
        conn.close()
        set_cache(cache_key, devices)
    
    detalle = None
    if selected_device_id:
        # Cache para detalles específicos del dispositivo
        detail_cache_key = f"device_detail_{selected_device_id}"
        detalle = get_cache(detail_cache_key)
        
        if not detalle:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT name, ip_address, created_at FROM devices WHERE id = ? AND user_id = ?", (selected_device_id, user_id))
            row = c.fetchone()
            
            if row:
                device_name, ip_address, fecha_registro = row
                c.execute("SELECT timestamp, consumption_kwh FROM consumption WHERE device_id = ? ORDER BY timestamp DESC LIMIT 20", (selected_device_id,))
                historial = c.fetchall()
                
                # Obtener consumo estimado (rápido, usa cache)
                consumo_estimado, fuente = obtener_consumo_completo(device_name)
                
                # Obtener fragmentos en background (no bloquea)
                fragmentos = obtener_fragmentos_google(device_name)
                
                detalle = {
                    'device_name': device_name,
                    'ip_address': ip_address,
                    'fecha_registro': fecha_registro,
                    'consumo_estimado': consumo_estimado,
                    'fuente_consumo': fuente,
                    'fragmentos': fragmentos,
                    'historial': historial
                }
                
                # Cache por 5 minutos
                set_cache(detail_cache_key, detalle)
            
            conn.close()
    
    return render_template('detalles_dispositivos.html', devices=devices, detalle=detalle, selected_device_id=selected_device_id)


@app.route('/dispositivos', methods=['GET', 'POST'])
def dispositivos():
    if 'username' not in session:
        return redirect(url_for('login'))
    energy_data = get_energy_data(session['receipt_number'])
    if request.method == 'POST':
        device_id = int(request.form['device_id'])
        action = request.form['action']
        receipt_number = session['receipt_number']
        user = get_user_by_receipt(receipt_number)
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        user_id = user[0]
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT ip_address FROM devices WHERE user_id = ? AND id = ?", (user_id, device_id))
        ip_address = c.fetchone()
        if ip_address:
            ip_address = ip_address[0]
            try:
                async def control_plug():
                    plug = SmartPlug(ip_address)
                    await plug.update()
                    if action == 'on':
                        await plug.turn_on()
                    else:
                        await plug.turn_off()
                    return f"Dispositivo {device_id} {'encendido' if action == 'on' else 'apagado'}"
                
                message = asyncio.run(control_plug())
                return jsonify({"message": message})
            except Exception as e:
                logging.error(f"Error al controlar dispositivo: {e}")
                return jsonify({"error": "Error al controlar dispositivo"}), 500
        conn.close()
    user = get_user_by_receipt(session['receipt_number'])
    plug_ids = set()
    if user:
        user_id = user[0]
        plug_ids = {row[0] for row in get_devices_by_user(user_id)}
    return render_template('dispositivos.html', devices=energy_data, plug_ids=plug_ids)

@app.route('/api/control_device', methods=['POST'])
def control_device():
    if 'username' not in session:
        return jsonify({"error": "No autenticado"}), 401
    device_id = int(request.json['device_id'])
    action = request.json['action']
    receipt_number = session['receipt_number']
    user = get_user_by_receipt(receipt_number)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    user_id = user[0]
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT ip_address FROM devices WHERE user_id = ? AND id = ?", (user_id, device_id))
    ip_address = c.fetchone()
    if ip_address:
        ip_address = ip_address[0]
        try:
            async def control_plug():
                plug = SmartPlug(ip_address)
                await plug.update()
                if action == 'on':
                    await plug.turn_on()
                else:
                    await plug.turn_off()
                return f"Dispositivo {device_id} {'encendido' if action == 'on' else 'apagado'}"
            
            message = asyncio.run(control_plug())
            return jsonify({"message": message})
        except Exception as e:
            logging.error(f"Error al controlar dispositivo: {e}")
            return jsonify({"error": "Error al controlar dispositivo"}), 500
    conn.close()
    return jsonify({"error": "Dispositivo no encontrado"}), 404

@app.route('/delete_device', methods=['POST'])
def delete_device():
    """
    Elimina un dispositivo del usuario autenticado por su ID.
    """
    if 'username' not in session:
        return redirect(url_for('login'))
    device_id = int(request.form['device_id'])
    user = get_user_by_receipt(session['receipt_number'])
    if not user:
        return redirect(url_for('dispositivos'))
    user_id = user[0]
    conn = get_db_connection()
    c = conn.cursor()
    # Solo permite eliminar dispositivos del usuario autenticado
    c.execute("DELETE FROM devices WHERE id = ? AND user_id = ?", (device_id, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for('dispositivos'))

@app.route('/add_plug', methods=['POST'])
def add_plug():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    device_description = request.form['device_description']
    ip_address = request.form['ip_address']
    receipt_number = session['receipt_number']
    
    if not device_description or not ip_address:
        return render_template('dispositivos.html', devices=get_energy_data(receipt_number), error="Descripción e IP son obligatorios.")
    
    try:
        octets = ip_address.split('.')
        if len(octets) != 4 or not all(o.isdigit() and 0 <= int(o) <= 255 for o in octets):
            return render_template('dispositivos.html', devices=get_energy_data(receipt_number), error="IP inválida.")
    except:
        return render_template('dispositivos.html', devices=get_energy_data(receipt_number), error="IP inválida.")
    
    user = get_user_by_receipt(receipt_number)
    if user:
        user_id = user[0]
        try:
            conn = get_db_connection()
            c = conn.cursor()
            fecha_lima = datetime.now(LIMA_TZ).strftime('%Y-%m-%d %H:%M:%S')
            c.execute("INSERT INTO devices (user_id, name, ip_address, created_at) VALUES (?, ?, ?, ?)",
                      (user_id, device_description, ip_address, fecha_lima))
            conn.commit()
            conn.close()
            
            # Limpiar cache relacionado
            clear_cache_pattern(f"devices_user_{user_id}")
            clear_cache_pattern(f"energy_data_user_{receipt_number}")
            clear_cache_pattern(f"dashboard_{receipt_number}")
            
            # Obtener consumo estimado en background
            def get_consumption_async():
                return obtener_consumo_completo(device_description)
            
            future = executor.submit(get_consumption_async)
            try:
                consumo_estimado, fuente = future.result(timeout=1)
                msg = f"Dispositivo agregado. Consumo estimado: {consumo_estimado} kWh/día (fuente: {fuente})." if consumo_estimado else "Dispositivo agregado exitosamente."
            except:
                msg = "Dispositivo agregado exitosamente."
            
            return render_template('dispositivos.html', devices=get_energy_data(receipt_number), success_message=msg)
        except sqlite3.IntegrityError:
            return render_template('dispositivos.html', devices=get_energy_data(receipt_number), error="La IP ya está registrada.")
    
    return render_template('dispositivos.html', devices=get_energy_data(receipt_number), error="Error al registrar el enchufe.")

@app.route('/recommendations')
def recommendations():
    if 'username' not in session:
        return redirect(url_for('login'))
    energy_data = get_energy_data(session['receipt_number'])
    total_consumption = sum(device['consumption'] for device in energy_data)
    recommendations = get_recommendations(total_consumption, energy_data, session['receipt_number'])
    return render_template('recommendations.html', recommendations=recommendations)

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    """
    Permite a los usuarios restablecer su contraseña si tienen problemas con hash incompatibles
    """
    if request.method == 'POST':
        username = request.form['username'].strip()
        dni = request.form['dni'].strip()
        new_password = request.form['new_password']
        
        if not username or not dni or not new_password:
            return render_template('reset_password.html', error="Todos los campos son obligatorios.")
        
        # Verificar que el usuario existe y el DNI coincide
        user = get_user_by_username(username)
        if not user or user[4] != dni:  # user[4] es el DNI
            return render_template('reset_password.html', error="Usuario no encontrado o DNI incorrecto.")
        
        # Actualizar la contraseña con un hash compatible
        new_hashed_password = safe_generate_password_hash(new_password)
        
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("UPDATE users SET password = ? WHERE username = ?", (new_hashed_password, username))
            conn.commit()
            conn.close()
            
            session['success_message'] = "Contraseña actualizada exitosamente. Ahora puedes iniciar sesión."
            return redirect(url_for('login'))
        except Exception as e:
            logging.error(f"Error al actualizar contraseña: {e}")
            return render_template('reset_password.html', error="Error al actualizar la contraseña.")
    
    return render_template('reset_password.html')

@app.route('/complete_profile', methods=['GET', 'POST'])
def complete_profile():
    """Permite a usuarios de Google completar su perfil"""
    if 'username' not in session or session.get('auth_method') != 'google':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        dni = request.form.get('dni', '').strip()
        receipt_number = request.form.get('receipt_number', '').strip()
        
        # Validaciones
        if dni and (not dni.isdigit() or len(dni) != 8):
            return render_template('complete_profile.html', error="El DNI debe contener exactamente 8 dígitos numéricos.")
        
        if receipt_number and (not receipt_number.isdigit() or not (6 <= len(receipt_number) <= 8)):
            return render_template('complete_profile.html', error="El número de recibo debe contener entre 6 y 8 dígitos numéricos.")
        
        if phone and not phone.isdigit():
            return render_template('complete_profile.html', error="El número de teléfono debe contener solo números.")
        
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # Verificar si DNI o recibo ya existen
            if dni:
                c.execute("SELECT id FROM users WHERE dni = ? AND id != ?", (dni, session['user_id']))
                if c.fetchone():
                    conn.close()
                    return render_template('complete_profile.html', error="El DNI ya está registrado por otro usuario.")
            
            if receipt_number:
                c.execute("SELECT id FROM users WHERE receipt_number = ? AND id != ?", (receipt_number, session['user_id']))
                if c.fetchone():
                    conn.close()
                    return render_template('complete_profile.html', error="El número de recibo ya está registrado por otro usuario.")
            
            # Actualizar perfil
            c.execute("""UPDATE users 
                         SET phone = ?, dni = ?, receipt_number = ? 
                         WHERE id = ?""",
                      (phone or None, dni or None, receipt_number or None, session['user_id']))
            conn.commit()
            conn.close()
            
            # Actualizar sesión
            if receipt_number:
                session['receipt_number'] = receipt_number
            
            # Limpiar cache
            clear_cache_pattern(f"user_google_{session.get('google_id')}")
            clear_cache_pattern(f"user_email_{session.get('email')}")
            
            session['success_message'] = "Perfil completado exitosamente."
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            logging.error(f"Error completando perfil: {e}")
            return render_template('complete_profile.html', error="Error al actualizar el perfil.")
    
    return render_template('complete_profile.html')

@app.route('/configuracion_correo')
def configuracion_correo():
    """Página de configuración de correo electrónico"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return render_template('configuracion_correo.html')

@app.route('/logout')
def logout():
    # Limpiar todas las variables de sesión
    session.clear()
    return redirect(url_for('login'))

@app.route('/auth/clear')
def clear_oauth_session():
    """Limpia la sesión OAuth en caso de problemas"""
    # Limpiar solo las variables relacionadas con OAuth
    oauth_keys = ['oauth_nonce', 'oauth_state', '_google_authlib_state_', '_google_authlib_nonce_']
    for key in oauth_keys:
        session.pop(key, None)
    
    return redirect(url_for('login'))

@app.route('/api/consumo_dispositivo/<int:device_id>')
def api_consumo_dispositivo(device_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT ip_address FROM devices WHERE id = ?", (device_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Dispositivo no encontrado"}), 404
    ip_address = row[0]
    try:
        async def get_consumption():
            plug = SmartPlug(ip_address)
            await plug.update()
            consumo = plug.emeter_realtime.get("power", 0) / 1000  # kWh
            return round(consumo, 3)
        
        consumo_actual = asyncio.run(get_consumption())
        return jsonify({"consumo_actual": consumo_actual})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/energy_data')
def api_energy_data():
    if 'username' not in session:
        return jsonify({"error": "No autenticado"}), 401
    return jsonify(get_energy_data(session['receipt_number']))

@app.route('/api/run_automation')
def run_automation():
    if 'username' not in session:
        return jsonify({"error": "No autenticado"}), 401
    check_automation_rules()
    return jsonify({"message": "Reglas de automatización ejecutadas"})

@app.route('/test_google_api')
def test_google_api():
    """
    Ruta de prueba para verificar si la API de Google está funcionando
    """
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Dispositivo de prueba
    test_device = "refrigerador"
    
    logging.info("=== INICIANDO PRUEBA DE API GOOGLE ===")
    
    # Probar obtener consumo
    consumo, fuente = obtener_consumo_completo(test_device)
    
    # Probar obtener fragmentos
    fragmentos = obtener_fragmentos_google(test_device)
    
    # Probar también la base de datos local
    consumo_local = obtener_consumo_local(test_device)
    
    result = {
        "dispositivo_prueba": test_device,
        "consumo_encontrado": consumo,
        "fuente_consumo": fuente,
        "consumo_local_disponible": consumo_local,
        "fragmentos_encontrados": len(fragmentos),
        "fragmentos": fragmentos[:3],  # Solo los primeros 3 para la prueba
        "api_key_configurada": bool(GOOGLE_API_KEY),
        "cx_configurado": bool(GOOGLE_CX),
        "dispositivos_en_base_local": len(CONSUMOS_TIPICOS)
    }
    
    logging.info(f"=== RESULTADO PRUEBA: {result} ===")
    
    return jsonify(result)

@app.route('/preview_email/<tipo>')
def preview_email(tipo):
    """
    Ruta para previsualizar los correos de bienvenida
    """
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Datos de ejemplo para la previsualización
    template_data = {
        'nombre': session.get('username', 'Usuario Ejemplo'),
        'fecha_actual': datetime.now(LIMA_TZ).strftime('%d de %B de %Y'),
        'fecha_login': datetime.now(LIMA_TZ).strftime('%d/%m/%Y a las %H:%M'),
        'dias_activo': 15,
        'dispositivos_conectados': 2,
        'ahorro_estimado': 28,
        'co2_reducido': 12,
        'consumo_mes': 45.5
    }
    
    if tipo == 'nuevo':
        template_name = 'email_bienvenida.html'
    elif tipo == 'vuelta':
        template_name = 'email_bienvenida_vuelta.html'
    else:
        return "Tipo de correo no válido. Usa 'nuevo' o 'vuelta'", 400
    
    try:
        return render_template(template_name, **template_data)
    except Exception as e:
        return f"Error renderizando template: {e}", 500

@app.route('/test_email', methods=['GET', 'POST'])
def test_email():
    """
    Ruta para probar el envío de correos de bienvenida
    """
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        email_destino = request.form.get('email')
        tipo_correo = request.form.get('tipo', 'nuevo')
        nombre = request.form.get('nombre', session.get('username', 'Usuario de Prueba'))
        
        if not email_destino:
            return jsonify({"error": "Email de destino requerido"}), 400
        
        es_nuevo = tipo_correo == 'nuevo'
        user_id = session.get('user_id') if not es_nuevo else None
        
        try:
            success = enviar_correo_bienvenida(email_destino, nombre, es_nuevo, user_id)
            if success:
                return jsonify({"message": f"Correo de {'bienvenida' if es_nuevo else 'regreso'} enviado exitosamente a {email_destino}"})
            else:
                return jsonify({"error": "Error al enviar el correo"}), 500
        except Exception as e:
            return jsonify({"error": f"Error: {str(e)}"}), 500
    
    # Mostrar formulario de prueba
    return render_template('test_email.html')

@app.route('/debug_oauth')
def debug_oauth():
    """
    Ruta de diagnóstico para verificar la configuración de OAuth
    """
    debug_info = {
        "GOOGLE_CLIENT_ID_exists": bool(os.environ.get('GOOGLE_CLIENT_ID')),
        "GOOGLE_CLIENT_SECRET_exists": bool(os.environ.get('GOOGLE_CLIENT_SECRET')),
        "GOOGLE_CLIENT_ID_value": os.environ.get('GOOGLE_CLIENT_ID', 'NO_SET')[:20] + "..." if os.environ.get('GOOGLE_CLIENT_ID') else "NO_SET",
        "GOOGLE_CLIENT_SECRET_value": os.environ.get('GOOGLE_CLIENT_SECRET', 'NO_SET')[:10] + "..." if os.environ.get('GOOGLE_CLIENT_SECRET') else "NO_SET",
        "GOOGLE_OAUTH_ENABLED": GOOGLE_OAUTH_ENABLED,
        "google_object_exists": google is not None,
        "environment": os.environ.get('FLASK_ENV', 'development'),
        "all_env_vars": list(os.environ.keys())
    }
    
    return jsonify(debug_info)

@app.route('/test_oauth_endpoints')
def test_oauth_endpoints():
    """
    Ruta para verificar los endpoints de OAuth que está usando Google
    """
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if not GOOGLE_OAUTH_ENABLED or not google:
        return jsonify({"error": "Google OAuth no está configurado"})
    
    try:
        # Obtener la metadata del servidor
        metadata = google.load_server_metadata()
        
        endpoints_info = {
            "authorization_endpoint": metadata.get('authorization_endpoint'),
            "token_endpoint": metadata.get('token_endpoint'),
            "userinfo_endpoint": metadata.get('userinfo_endpoint'),
            "jwks_uri": metadata.get('jwks_uri'),
            "issuer": metadata.get('issuer'),
            "revocation_endpoint": metadata.get('revocation_endpoint'),
            "scopes_supported": metadata.get('scopes_supported'),
            "response_types_supported": metadata.get('response_types_supported')
        }
        
        return jsonify({
            "status": "success",
            "message": "Endpoints de Google OAuth cargados correctamente",
            "endpoints": endpoints_info
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error al cargar endpoints: {str(e)}"
        })

@app.route('/debug/session')
def debug_session():
    """
    Ruta de debug para verificar el estado de la sesión
    """
    session_info = {
        "session_keys": list(session.keys()),
        "oauth_keys": {k: v for k, v in session.items() if 'oauth' in k.lower() or 'google' in k.lower() or 'authlib' in k.lower()},
        "flask_secret_key_set": bool(app.secret_key),
        "google_oauth_enabled": GOOGLE_OAUTH_ENABLED,
        "google_client_id": GOOGLE_CLIENT_ID[:10] + "..." if GOOGLE_CLIENT_ID else None,
        "redirect_uri": url_for('google_callback', _external=True)
    }
    
    return jsonify(session_info)

@app.route('/debug/oauth_config')
def debug_oauth_config():
    """
    Ruta de debug para verificar la configuración OAuth
    """
    config_info = {
        "google_oauth_enabled": GOOGLE_OAUTH_ENABLED,
        "google_client_id_set": bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_ID != 'tu_google_client_id_aqui'),
        "google_client_secret_set": bool(GOOGLE_CLIENT_SECRET and GOOGLE_CLIENT_SECRET != 'tu_google_client_secret_aqui'),
        "google_client_id_prefix": GOOGLE_CLIENT_ID[:20] + "..." if GOOGLE_CLIENT_ID else None,
        "redirect_uri": url_for('google_callback', _external=True),
        "authorization_url": url_for('google_login', _external=True),
        "flask_secret_key_length": len(app.secret_key) if app.secret_key else 0,
        "session_config": {
            "SESSION_COOKIE_SECURE": app.config.get('SESSION_COOKIE_SECURE'),
            "SESSION_COOKIE_HTTPONLY": app.config.get('SESSION_COOKIE_HTTPONLY'),
            "SESSION_COOKIE_SAMESITE": app.config.get('SESSION_COOKIE_SAMESITE'),
        }
    }
    
    return jsonify(config_info)

@app.route('/test/oauth_flow')
def test_oauth_flow():
    """
    Ruta de prueba para verificar el flujo OAuth completo
    """
    if not GOOGLE_OAUTH_ENABLED:
        return jsonify({"error": "Google OAuth no está habilitado"})
    
    # Construir URL de autorización manual
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={url_for('google_callback', _external=True)}"
        f"&response_type=code"
        f"&scope=openid email profile"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    
    test_info = {
        "status": "ready",
        "google_oauth_enabled": GOOGLE_OAUTH_ENABLED,
        "client_id": GOOGLE_CLIENT_ID[:20] + "..." if GOOGLE_CLIENT_ID else None,
        "redirect_uri": url_for('google_callback', _external=True),
        "authorization_url": auth_url,
        "instructions": [
            "1. Copia la authorization_url",
            "2. Pégala en tu navegador",
            "3. Autoriza la aplicación",
            "4. Deberías ser redirigido al callback",
            "5. Revisa los logs de la aplicación"
        ]
    }
    
    return jsonify(test_info)

@app.route('/debug/mail_config')
def debug_mail_config():
    """
    Ruta de debug para verificar la configuración de correo
    """
    mail_config = {
        "mail_server": app.config.get('MAIL_SERVER'),
        "mail_port": app.config.get('MAIL_PORT'),
        "mail_use_tls": app.config.get('MAIL_USE_TLS'),
        "mail_use_ssl": app.config.get('MAIL_USE_SSL'),
        "mail_username_set": bool(app.config.get('MAIL_USERNAME') and app.config.get('MAIL_USERNAME') != 'tu_email@gmail.com'),
        "mail_password_set": bool(app.config.get('MAIL_PASSWORD') and app.config.get('MAIL_PASSWORD') != 'tu_app_password_aqui'),
        "mail_default_sender": app.config.get('MAIL_DEFAULT_SENDER'),
        "configuracion_completa": verificar_configuracion_correo(),
        "instrucciones": [
            "1. Configura MAIL_USERNAME con tu email de Gmail",
            "2. Configura MAIL_PASSWORD con tu App Password de Gmail",
            "3. Configura MAIL_DEFAULT_SENDER con tu email",
            "4. Para obtener App Password: https://myaccount.google.com/apppasswords"
        ]
    }
    
    return jsonify(mail_config)

@app.route('/test/send_email', methods=['POST'])
def test_send_email():
    """
    Ruta para probar el envío de correos
    """
    if 'username' not in session:
        return jsonify({"error": "No autenticado"}), 401
    
    try:
        data = request.get_json()
        email_destino = data.get('email')
        
        if not email_destino:
            return jsonify({"error": "Email de destino requerido"}), 400
        
        success, message = enviar_correo_test(email_destino)
        
        if success:
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"success": False, "error": message}), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/test/welcome_email', methods=['POST'])
def test_welcome_email():
    """
    Ruta para probar el correo de bienvenida
    """
    if 'username' not in session:
        return jsonify({"error": "No autenticado"}), 401
    
    try:
        data = request.get_json()
        email_destino = data.get('email')
        nombre = data.get('nombre', 'Usuario de Prueba')
        es_nuevo = data.get('es_nuevo_usuario', True)
        
        if not email_destino:
            return jsonify({"error": "Email de destino requerido"}), 400
        
        success = enviar_correo_bienvenida(email_destino, nombre, es_nuevo)
        
        if success:
            return jsonify({"success": True, "message": "Correo de bienvenida enviado"})
        else:
            return jsonify({"success": False, "error": "Error enviando correo de bienvenida"}), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def migrate_scrypt_passwords():
    """
    Migra contraseñas con hash scrypt incompatible.
    NOTA: Esta función solo puede usarse si tienes acceso a las contraseñas originales.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, password FROM users")
    users = c.fetchall()
    
    migrated_count = 0
    for user_id, username, password_hash in users:
        if password_hash.startswith('scrypt:'):
            logging.info(f"Usuario {username} tiene hash scrypt incompatible. Requiere restablecimiento manual.")
            migrated_count += 1
    
    conn.close()
    
    if migrated_count > 0:
        logging.warning(f"Se encontraron {migrated_count} usuarios con hash scrypt. "
                       f"Estos usuarios necesitarán restablecer su contraseña usando /reset_password")
    else:
        logging.info("No se encontraron usuarios con hash scrypt incompatible.")
    
    return migrated_count

def start_automation_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_automation_rules, 'interval', minutes=5)
    scheduler.start()

if __name__ == '__main__':
    # Verificar y reportar usuarios con hash scrypt incompatible
    migrate_scrypt_passwords()
    
    start_automation_scheduler()
    app.run(debug=True)
