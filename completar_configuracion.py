#!/usr/bin/env python3
"""
Script final para completar la configuración de EnerVirgil con Google OAuth
"""

import os
import sqlite3
import sys

def cargar_variables_env():
    """Carga variables de entorno desde archivo .env"""
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        return True
    return False

def completar_migracion_bd():
    """Completa la migración de la base de datos"""
    print("🔧 Completando migración de base de datos...")
    
    try:
        conn = sqlite3.connect('ener_virgil.db')
        c = conn.cursor()
        
        # Verificar y agregar columnas faltantes
        c.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in c.fetchall()]
        
        columnas_faltantes = []
        
        if 'google_id' not in columns:
            c.execute('ALTER TABLE users ADD COLUMN google_id TEXT UNIQUE')
            columnas_faltantes.append('google_id')
        
        if 'created_at' not in columns:
            c.execute('ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP')
            columnas_faltantes.append('created_at')
        
        # Crear índices faltantes
        try:
            c.execute('CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id)')
        except:
            pass
        
        conn.commit()
        conn.close()
        
        if columnas_faltantes:
            print(f"✅ Columnas agregadas: {', '.join(columnas_faltantes)}")
        else:
            print("✅ Base de datos ya está completa")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en migración: {e}")
        return False

def verificar_configuracion_completa():
    """Verifica que toda la configuración esté completa"""
    print("\n🔍 Verificación final de configuración...")
    
    # Verificar archivo .env
    if not os.path.exists('.env'):
        print("❌ Archivo .env no encontrado")
        return False
    
    # Verificar variables de entorno
    client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    
    if not client_id or client_id == 'tu_google_client_id_aqui':
        print("❌ GOOGLE_CLIENT_ID no configurado")
        return False
    
    if not client_secret or client_secret == 'tu_google_client_secret_aqui':
        print("❌ GOOGLE_CLIENT_SECRET no configurado")
        return False
    
    # Verificar base de datos
    try:
        conn = sqlite3.connect('ener_virgil.db')
        c = conn.cursor()
        c.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in c.fetchall()]
        conn.close()
        
        columnas_requeridas = ['id', 'username', 'full_name', 'phone', 'dni', 'receipt_number', 'password', 'google_id', 'email', 'profile_picture', 'auth_method', 'created_at']
        
        for col in columnas_requeridas:
            if col not in columns:
                print(f"❌ Columna faltante en BD: {col}")
                return False
        
    except Exception as e:
        print(f"❌ Error verificando BD: {e}")
        return False
    
    # Verificar archivos de la aplicación
    archivos_requeridos = ['app.py', 'requirements.txt', 'templates/login.html', 'templates/complete_profile.html']
    
    for archivo in archivos_requeridos:
        if not os.path.exists(archivo):
            print(f"❌ Archivo faltante: {archivo}")
            return False
    
    print("✅ Configuración completa y válida")
    return True

def mostrar_resumen_final():
    """Muestra el resumen final de la configuración"""
    print("\n" + "="*60)
    print("🎉 CONFIGURACIÓN COMPLETADA EXITOSAMENTE")
    print("="*60)
    
    print("\n📋 FUNCIONALIDADES DISPONIBLES:")
    print("✅ Login tradicional (usuario/contraseña)")
    print("✅ Login con Google OAuth")
    print("✅ Registro de nuevos usuarios")
    print("✅ Dashboard de consumo energético")
    print("✅ Gestión de dispositivos TP-Link")
    print("✅ Recomendaciones de ahorro")
    print("✅ Detalles de dispositivos")
    print("✅ Completar perfil para usuarios de Google")
    print("✅ Sistema híbrido de autenticación")
    
    print("\n🚀 CÓMO INICIAR LA APLICACIÓN:")
    print("Opción 1 (Recomendada):")
    print("  📁 Doble clic en: iniciar_con_google.bat")
    
    print("\nOpción 2 (Manual):")
    print("  💻 python cargar_env_y_ejecutar.py")
    
    print("\nOpción 3 (Avanzada):")
    print("  🔧 Configurar variables de entorno manualmente")
    print("  🔧 python app.py")
    
    print("\n🌐 ACCESO A LA APLICACIÓN:")
    print("  📱 URL: http://localhost:5000")
    print("  👤 Login tradicional: Usa tu usuario/contraseña existente")
    print("  🔗 Login con Google: Haz clic en 'Iniciar sesión con Google'")
    
    print("\n💡 NOTAS IMPORTANTES:")
    print("  🔒 Las credenciales están seguras en .env")
    print("  📊 La base de datos se migró automáticamente")
    print("  🔄 Usuarios existentes siguen funcionando normalmente")
    print("  🆕 Nuevos usuarios pueden usar Google o registro tradicional")
    
    print("\n🛠️ ARCHIVOS CREADOS:")
    print("  📄 .env - Variables de entorno")
    print("  🚀 iniciar_con_google.bat - Script de inicio")
    print("  🔧 cargar_env_y_ejecutar.py - Cargador de variables")
    print("  📋 complete_profile.html - Template para completar perfil")
    
    print("\n" + "="*60)

def main():
    print("🔧 COMPLETANDO CONFIGURACIÓN DE ENERVIRGIL")
    print("="*50)
    
    # Cargar variables de entorno
    print("📋 Cargando variables de entorno...")
    if cargar_variables_env():
        print("✅ Variables de entorno cargadas")
    else:
        print("⚠️ No se encontró archivo .env")
    
    # Completar migración de BD
    if not completar_migracion_bd():
        print("❌ Error completando migración")
        return False
    
    # Verificar configuración completa
    if not verificar_configuracion_completa():
        print("❌ Configuración incompleta")
        return False
    
    # Mostrar resumen final
    mostrar_resumen_final()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎊 ¡TODO LISTO! EnerVirgil está completamente configurado.")
            print("🚀 Ejecuta 'iniciar_con_google.bat' para comenzar")
        else:
            print("\n😞 Configuración incompleta")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    input("\nPresiona ENTER para continuar...")