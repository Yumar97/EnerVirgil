#!/usr/bin/env python3
"""
Script para reparar y verificar la base de datos de EnerVirgil
"""

import os
import sys
import sqlite3
from datetime import datetime

# Cargar variables de entorno
sys.path.insert(0, '.')
import load_env

DB_PATH = 'ener_virgil.db'

def verificar_estructura_db():
    """Verifica la estructura actual de la base de datos"""
    print("🔍 VERIFICANDO ESTRUCTURA DE BASE DE DATOS")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        c = conn.cursor()
        
        # Verificar tabla users
        print("\n📋 TABLA USERS:")
        c.execute("PRAGMA table_info(users)")
        columns = c.fetchall()
        
        for col in columns:
            col_id, name, type_, notnull, default, pk = col
            nullable = "NOT NULL" if notnull else "NULL"
            pk_info = "PRIMARY KEY" if pk else ""
            print(f"   {name}: {type_} {nullable} {pk_info}")
        
        # Verificar si existen las columnas de Google OAuth
        column_names = [col[1] for col in columns]
        google_columns = ['google_id', 'email', 'profile_picture', 'auth_method', 'created_at']
        
        print(f"\n🔍 COLUMNAS DE GOOGLE OAUTH:")
        for col in google_columns:
            status = "✅" if col in column_names else "❌"
            print(f"   {status} {col}")
        
        # Verificar índices
        print(f"\n📋 ÍNDICES:")
        c.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='users'")
        indices = c.fetchall()
        for idx in indices:
            print(f"   ✅ {idx[0]}")
        
        # Contar usuarios
        c.execute("SELECT COUNT(*) FROM users")
        user_count = c.fetchone()[0]
        print(f"\n👥 USUARIOS TOTALES: {user_count}")
        
        # Contar usuarios de Google
        if 'auth_method' in column_names:
            c.execute("SELECT COUNT(*) FROM users WHERE auth_method = 'google'")
            google_users = c.fetchone()[0]
            print(f"👥 USUARIOS DE GOOGLE: {google_users}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")
        return False

def reparar_base_datos():
    """Repara la base de datos agregando columnas faltantes"""
    print("\n🔧 REPARANDO BASE DE DATOS")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        c = conn.cursor()
        
        # Verificar columnas existentes
        c.execute("PRAGMA table_info(users)")
        existing_columns = [col[1] for col in c.fetchall()]
        
        # Columnas que necesitamos para Google OAuth
        required_columns = [
            ('google_id', 'TEXT UNIQUE'),
            ('email', 'TEXT'),
            ('profile_picture', 'TEXT'),
            ('auth_method', 'TEXT DEFAULT "local"'),
            ('created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP')
        ]
        
        changes_made = False
        
        for column_name, column_type in required_columns:
            if column_name not in existing_columns:
                try:
                    print(f"   ➕ Agregando columna: {column_name}")
                    c.execute(f'ALTER TABLE users ADD COLUMN {column_name} {column_type}')
                    changes_made = True
                except sqlite3.OperationalError as e:
                    print(f"   ⚠️ Error agregando {column_name}: {e}")
        
        # Hacer campos opcionales para usuarios de Google
        print(f"   🔧 Haciendo campos opcionales para usuarios de Google...")
        
        # Crear índices si no existen
        indices_to_create = [
            ('idx_users_google_id', 'CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id)'),
            ('idx_users_email', 'CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)'),
            ('idx_users_auth_method', 'CREATE INDEX IF NOT EXISTS idx_users_auth_method ON users(auth_method)')
        ]
        
        for idx_name, idx_sql in indices_to_create:
            try:
                c.execute(idx_sql)
                print(f"   ✅ Índice creado: {idx_name}")
            except Exception as e:
                print(f"   ⚠️ Error creando índice {idx_name}: {e}")
        
        if changes_made:
            conn.commit()
            print(f"   ✅ Cambios guardados en la base de datos")
        else:
            print(f"   ℹ️ No se necesitaron cambios")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error reparando base de datos: {e}")
        return False

def crear_usuario_prueba_google():
    """Crea un usuario de prueba para Google OAuth"""
    print("\n🧪 CREANDO USUARIO DE PRUEBA GOOGLE")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        c = conn.cursor()
        
        # Verificar si ya existe un usuario de prueba
        c.execute("SELECT id FROM users WHERE username = 'test_google_user'")
        if c.fetchone():
            print("   ℹ️ Usuario de prueba ya existe")
            conn.close()
            return True
        
        # Crear usuario de prueba
        test_data = {
            'username': 'test_google_user',
            'full_name': 'Usuario de Prueba Google',
            'phone': None,
            'dni': None,
            'receipt_number': None,
            'password': '',
            'email': 'test@gmail.com',
            'google_id': 'test_google_id_123',
            'profile_picture': None,
            'auth_method': 'google',
            'created_at': datetime.now()
        }
        
        c.execute("""INSERT INTO users 
                     (username, full_name, phone, dni, receipt_number, password, 
                      email, google_id, profile_picture, auth_method, created_at) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (test_data['username'], test_data['full_name'], test_data['phone'],
                   test_data['dni'], test_data['receipt_number'], test_data['password'],
                   test_data['email'], test_data['google_id'], test_data['profile_picture'],
                   test_data['auth_method'], test_data['created_at']))
        
        user_id = c.lastrowid
        conn.commit()
        conn.close()
        
        print(f"   ✅ Usuario de prueba creado con ID: {user_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error creando usuario de prueba: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def limpiar_usuarios_prueba():
    """Limpia usuarios de prueba"""
    print("\n🧹 LIMPIANDO USUARIOS DE PRUEBA")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        c = conn.cursor()
        
        # Eliminar usuarios de prueba
        c.execute("DELETE FROM users WHERE username LIKE 'test_%' OR google_id LIKE 'test_%'")
        deleted = c.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ {deleted} usuarios de prueba eliminados")
        return True
        
    except Exception as e:
        print(f"❌ Error limpiando usuarios de prueba: {e}")
        return False

def main():
    """Función principal"""
    print("🔧 REPARADOR DE BASE DE DATOS - ENERVIRGIL")
    print("=" * 60)
    
    # Verificar estructura actual
    if not verificar_estructura_db():
        print("❌ No se pudo verificar la base de datos")
        return
    
    # Reparar base de datos
    if not reparar_base_datos():
        print("❌ No se pudo reparar la base de datos")
        return
    
    # Verificar estructura después de reparar
    print("\n🔍 VERIFICANDO ESTRUCTURA DESPUÉS DE REPARAR")
    print("=" * 60)
    verificar_estructura_db()
    
    # Preguntar si crear usuario de prueba
    try:
        respuesta = input("\n¿Crear usuario de prueba para Google OAuth? (s/n): ")
        if respuesta.lower() in ['s', 'si', 'y', 'yes']:
            crear_usuario_prueba_google()
    except:
        pass
    
    print("\n✅ REPARACIÓN COMPLETADA")
    print("=" * 60)
    print("La base de datos ha sido reparada y está lista para Google OAuth")
    print("Puedes reiniciar la aplicación y probar el login con Google")

if __name__ == "__main__":
    main()