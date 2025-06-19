#!/usr/bin/env python3
"""
Script para migrar la base de datos de EnerVirgil a la nueva estructura con Google OAuth
"""

import os
import sys
import sqlite3
import shutil
from datetime import datetime

# Cargar variables de entorno
sys.path.insert(0, '.')
import load_env

DB_PATH = 'ener_virgil.db'
BACKUP_PATH = 'ener_virgil_backup.db'

def hacer_backup():
    """Hace backup de la base de datos actual"""
    print("💾 HACIENDO BACKUP DE LA BASE DE DATOS")
    print("=" * 60)
    
    try:
        if os.path.exists(DB_PATH):
            shutil.copy2(DB_PATH, BACKUP_PATH)
            print(f"✅ Backup creado: {BACKUP_PATH}")
            return True
        else:
            print("ℹ️ No existe base de datos para hacer backup")
            return True
    except Exception as e:
        print(f"❌ Error haciendo backup: {e}")
        return False

def migrar_tabla_users():
    """Migra la tabla users a la nueva estructura"""
    print("\n🔄 MIGRANDO TABLA USERS")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        c = conn.cursor()
        
        # Verificar si ya tiene la estructura correcta
        c.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in c.fetchall()]
        
        if 'google_id' in columns and 'created_at' in columns:
            print("✅ La tabla ya tiene la estructura correcta")
            conn.close()
            return True
        
        # Obtener datos existentes
        print("📋 Obteniendo datos existentes...")
        c.execute("SELECT * FROM users")
        existing_users = c.fetchall()
        
        # Obtener estructura actual
        c.execute("PRAGMA table_info(users)")
        old_columns = c.fetchall()
        
        print(f"📊 Usuarios existentes: {len(existing_users)}")
        
        # Crear nueva tabla con estructura completa
        print("🏗️ Creando nueva estructura de tabla...")
        c.execute('''DROP TABLE IF EXISTS users_new''')
        
        c.execute('''CREATE TABLE users_new
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT NOT NULL UNIQUE,
                      full_name TEXT NOT NULL,
                      phone TEXT,
                      dni TEXT UNIQUE,
                      receipt_number TEXT UNIQUE,
                      password TEXT,
                      email TEXT,
                      google_id TEXT UNIQUE,
                      profile_picture TEXT,
                      auth_method TEXT DEFAULT "local",
                      created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        
        # Migrar datos existentes
        if existing_users:
            print("📦 Migrando datos existentes...")
            for user in existing_users:
                # Mapear datos antiguos a nueva estructura
                old_id, username, full_name, phone, dni, receipt_number, password = user[:7]
                
                # Obtener campos adicionales si existen
                email = user[7] if len(user) > 7 and user[7] else None
                profile_picture = user[8] if len(user) > 8 and user[8] else None
                auth_method = user[9] if len(user) > 9 and user[9] else 'local'
                
                # Insertar en nueva tabla
                c.execute('''INSERT INTO users_new 
                             (username, full_name, phone, dni, receipt_number, password,
                              email, google_id, profile_picture, auth_method, created_at)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (username, full_name, phone, dni, receipt_number, password,
                           email, None, profile_picture, auth_method, datetime.now()))
            
            print(f"✅ {len(existing_users)} usuarios migrados")
        
        # Reemplazar tabla antigua
        print("🔄 Reemplazando tabla antigua...")
        c.execute('DROP TABLE users')
        c.execute('ALTER TABLE users_new RENAME TO users')
        
        # Crear índices
        print("📇 Creando índices...")
        indices = [
            'CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)',
            'CREATE INDEX IF NOT EXISTS idx_users_receipt ON users(receipt_number)',
            'CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)',
            'CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id)',
            'CREATE INDEX IF NOT EXISTS idx_users_auth_method ON users(auth_method)',
            'CREATE INDEX IF NOT EXISTS idx_users_dni ON users(dni)'
        ]
        
        for idx_sql in indices:
            c.execute(idx_sql)
        
        conn.commit()
        conn.close()
        
        print("✅ Migración de tabla users completada")
        return True
        
    except Exception as e:
        print(f"❌ Error migrando tabla users: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def verificar_migracion():
    """Verifica que la migración fue exitosa"""
    print("\n🔍 VERIFICANDO MIGRACIÓN")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        c = conn.cursor()
        
        # Verificar estructura
        c.execute("PRAGMA table_info(users)")
        columns = c.fetchall()
        
        print("📋 ESTRUCTURA FINAL:")
        for col in columns:
            col_id, name, type_, notnull, default, pk = col
            nullable = "NOT NULL" if notnull else "NULL"
            pk_info = "PRIMARY KEY" if pk else ""
            default_info = f"DEFAULT {default}" if default else ""
            print(f"   {name}: {type_} {nullable} {pk_info} {default_info}")
        
        # Verificar columnas requeridas
        column_names = [col[1] for col in columns]
        required_columns = ['google_id', 'email', 'profile_picture', 'auth_method', 'created_at']
        
        print(f"\n✅ COLUMNAS REQUERIDAS:")
        all_present = True
        for col in required_columns:
            if col in column_names:
                print(f"   ✅ {col}")
            else:
                print(f"   ❌ {col}")
                all_present = False
        
        # Contar usuarios
        c.execute("SELECT COUNT(*) FROM users")
        user_count = c.fetchone()[0]
        print(f"\n👥 USUARIOS TOTALES: {user_count}")
        
        # Verificar usuarios por método de autenticación
        c.execute("SELECT auth_method, COUNT(*) FROM users GROUP BY auth_method")
        auth_stats = c.fetchall()
        print(f"📊 USUARIOS POR MÉTODO:")
        for method, count in auth_stats:
            print(f"   {method}: {count}")
        
        conn.close()
        
        if all_present:
            print(f"\n🎉 MIGRACIÓN EXITOSA")
            return True
        else:
            print(f"\n❌ MIGRACIÓN INCOMPLETA")
            return False
        
    except Exception as e:
        print(f"❌ Error verificando migración: {e}")
        return False

def crear_usuario_prueba():
    """Crea un usuario de prueba para Google OAuth"""
    print("\n🧪 CREANDO USUARIO DE PRUEBA")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        c = conn.cursor()
        
        # Verificar si ya existe
        c.execute("SELECT id FROM users WHERE google_id = 'test_google_123'")
        if c.fetchone():
            print("ℹ️ Usuario de prueba ya existe")
            conn.close()
            return True
        
        # Crear usuario de prueba
        c.execute('''INSERT INTO users 
                     (username, full_name, phone, dni, receipt_number, password,
                      email, google_id, profile_picture, auth_method, created_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  ('test_google', 'Usuario Prueba Google', None, None, None, '',
                   'test@gmail.com', 'test_google_123', None, 'google', datetime.now()))
        
        user_id = c.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Usuario de prueba creado con ID: {user_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error creando usuario de prueba: {e}")
        return False

def main():
    """Función principal"""
    print("🔄 MIGRADOR DE BASE DE DATOS - ENERVIRGIL")
    print("=" * 60)
    print("Este script migrará tu base de datos para soportar Google OAuth")
    
    # Hacer backup
    if not hacer_backup():
        print("❌ No se pudo hacer backup. Abortando.")
        return
    
    # Migrar tabla users
    if not migrar_tabla_users():
        print("❌ Error en la migración. Restaurando backup...")
        try:
            shutil.copy2(BACKUP_PATH, DB_PATH)
            print("✅ Backup restaurado")
        except:
            print("❌ Error restaurando backup")
        return
    
    # Verificar migración
    if not verificar_migracion():
        print("❌ La migración no fue exitosa")
        return
    
    # Preguntar si crear usuario de prueba
    try:
        respuesta = input("\n¿Crear usuario de prueba para Google OAuth? (s/n): ")
        if respuesta.lower() in ['s', 'si', 'y', 'yes']:
            crear_usuario_prueba()
    except:
        pass
    
    print("\n🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 60)
    print("✅ La base de datos ha sido migrada correctamente")
    print("✅ Ahora soporta Google OAuth completamente")
    print("✅ Backup guardado en:", BACKUP_PATH)
    print("\n🚀 Puedes reiniciar la aplicación y probar Google OAuth")

if __name__ == "__main__":
    main()