#!/usr/bin/env python3
"""
Script para verificar la migración de la base de datos
"""

import sqlite3
import os

def verify_database():
    """Verifica que la base de datos tenga todas las columnas necesarias"""
    db_path = 'ener_virgil.db'
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return False
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:
        # Verificar estructura de la tabla users
        c.execute("PRAGMA table_info(users)")
        columns = {column[1]: column[2] for column in c.fetchall()}
        
        print("📋 Columnas actuales en la tabla 'users':")
        for col_name, col_type in columns.items():
            print(f"  - {col_name}: {col_type}")
        
        # Columnas requeridas
        required_columns = {
            'id': 'INTEGER',
            'username': 'TEXT',
            'full_name': 'TEXT',
            'phone': 'TEXT',
            'dni': 'TEXT',
            'receipt_number': 'TEXT',
            'password': 'TEXT'
        }
        
        # Columnas nuevas (opcionales)
        new_columns = {
            'google_id': 'TEXT',
            'email': 'TEXT',
            'profile_picture': 'TEXT',
            'auth_method': 'TEXT',
            'created_at': 'DATETIME'
        }
        
        print("\n✅ Verificación de columnas requeridas:")
        all_required_present = True
        for col_name in required_columns:
            if col_name in columns:
                print(f"  ✓ {col_name}")
            else:
                print(f"  ❌ {col_name} - FALTANTE")
                all_required_present = False
        
        print("\n🆕 Verificación de columnas nuevas:")
        new_columns_present = 0
        for col_name in new_columns:
            if col_name in columns:
                print(f"  ✓ {col_name}")
                new_columns_present += 1
            else:
                print(f"  ⚠️ {col_name} - No presente (se agregará automáticamente)")
        
        # Verificar índices
        c.execute("PRAGMA index_list(users)")
        indexes = [index[1] for index in c.fetchall()]
        
        print(f"\n📊 Índices encontrados: {len(indexes)}")
        for index in indexes:
            print(f"  - {index}")
        
        # Contar usuarios
        c.execute("SELECT COUNT(*) FROM users")
        user_count = c.fetchone()[0]
        print(f"\n👥 Usuarios en la base de datos: {user_count}")
        
        if user_count > 0:
            # Verificar tipos de usuarios
            if 'auth_method' in columns:
                c.execute("SELECT auth_method, COUNT(*) FROM users GROUP BY auth_method")
                auth_methods = c.fetchall()
                print("📈 Distribución por método de autenticación:")
                for method, count in auth_methods:
                    method_name = method if method else 'local (legacy)'
                    print(f"  - {method_name}: {count}")
        
        print(f"\n{'='*50}")
        if all_required_present:
            print("✅ La base de datos está lista para funcionar")
            if new_columns_present >= 3:
                print("✅ Las funciones de Google OAuth están disponibles")
            else:
                print("⚠️ Las funciones de Google OAuth se habilitarán automáticamente")
        else:
            print("❌ La base de datos necesita reparación")
        
        return all_required_present
        
    except Exception as e:
        print(f"❌ Error verificando la base de datos: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔍 Verificando migración de base de datos...\n")
    success = verify_database()
    
    if success:
        print("\n🚀 Puedes ejecutar la aplicación con: python app.py")
    else:
        print("\n🔧 Ejecuta la aplicación para que se realice la migración automática")