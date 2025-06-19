#!/usr/bin/env python3
"""
Test final del sistema OAuth de EnerVirgil después de la migración
"""

import os
import sys
import sqlite3

# Cargar variables de entorno
sys.path.insert(0, '.')
import load_env

# Importar funciones de la aplicación
from app import create_google_user, get_user_by_google_id, update_google_user_info

def test_base_datos():
    """Test de la base de datos migrada"""
    print("🧪 TEST DE BASE DE DATOS MIGRADA")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('ener_virgil.db', timeout=10)
        c = conn.cursor()
        
        # Verificar estructura
        c.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in c.fetchall()]
        
        required_columns = ['google_id', 'email', 'profile_picture', 'auth_method', 'created_at']
        
        print("📋 VERIFICANDO COLUMNAS:")
        all_present = True
        for col in required_columns:
            if col in columns:
                print(f"   ✅ {col}")
            else:
                print(f"   ❌ {col}")
                all_present = False
        
        if not all_present:
            print("❌ Faltan columnas requeridas")
            return False
        
        # Contar usuarios
        c.execute("SELECT COUNT(*) FROM users")
        total_users = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM users WHERE auth_method = 'google'")
        google_users = c.fetchone()[0]
        
        print(f"\n👥 USUARIOS:")
        print(f"   Total: {total_users}")
        print(f"   Google: {google_users}")
        print(f"   Local: {total_users - google_users}")
        
        conn.close()
        print("✅ Base de datos verificada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")
        return False

def test_funciones_google():
    """Test de las funciones de Google OAuth"""
    print("\n🧪 TEST DE FUNCIONES GOOGLE OAUTH")
    print("=" * 60)
    
    # Datos de prueba
    test_google_id = "test_oauth_final_123"
    test_email = "test_oauth_final@gmail.com"
    test_name = "Usuario Test OAuth Final"
    test_picture = "https://example.com/picture.jpg"
    
    try:
        # Test 1: Crear usuario
        print("📝 Test 1: Crear usuario de Google")
        user_id = create_google_user(test_google_id, test_email, test_name, test_picture)
        
        if user_id:
            print(f"   ✅ Usuario creado con ID: {user_id}")
        else:
            print("   ❌ Error creando usuario")
            return False
        
        # Test 2: Obtener usuario por Google ID
        print("📝 Test 2: Obtener usuario por Google ID")
        user = get_user_by_google_id(test_google_id)
        
        if user:
            print(f"   ✅ Usuario encontrado: {user[1]} ({user[7]})")  # username y email
        else:
            print("   ❌ Usuario no encontrado")
            return False
        
        # Test 3: Actualizar información
        print("📝 Test 3: Actualizar información del usuario")
        updated_name = "Usuario Test OAuth Final ACTUALIZADO"
        success = update_google_user_info(test_google_id, test_email, updated_name, test_picture)
        
        if success:
            print("   ✅ Usuario actualizado correctamente")
        else:
            print("   ❌ Error actualizando usuario")
            return False
        
        # Test 4: Verificar actualización
        print("📝 Test 4: Verificar actualización")
        updated_user = get_user_by_google_id(test_google_id)
        
        if updated_user and updated_user[2] == updated_name:  # full_name
            print(f"   ✅ Actualización verificada: {updated_user[2]}")
        else:
            print("   ❌ Actualización no se aplicó correctamente")
            return False
        
        # Limpiar usuario de prueba
        print("📝 Limpiando usuario de prueba")
        conn = sqlite3.connect('ener_virgil.db', timeout=10)
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE google_id = ?", (test_google_id,))
        conn.commit()
        conn.close()
        print("   ✅ Usuario de prueba eliminado")
        
        print("✅ Todas las funciones de Google OAuth funcionan correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en test de funciones: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_configuracion_oauth():
    """Test de la configuración OAuth"""
    print("\n🧪 TEST DE CONFIGURACIÓN OAUTH")
    print("=" * 60)
    
    # Verificar variables de entorno
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    flask_secret = os.environ.get('FLASK_SECRET_KEY')
    
    print("📋 VARIABLES DE ENTORNO:")
    if client_id and client_id != 'tu_google_client_id_aqui':
        print(f"   ✅ GOOGLE_CLIENT_ID: {client_id[:20]}...")
    else:
        print("   ❌ GOOGLE_CLIENT_ID no configurado")
        return False
    
    if client_secret and client_secret != 'tu_google_client_secret_aqui':
        print("   ✅ GOOGLE_CLIENT_SECRET: configurado")
    else:
        print("   ❌ GOOGLE_CLIENT_SECRET no configurado")
        return False
    
    if flask_secret:
        print("   ✅ FLASK_SECRET_KEY: configurado")
    else:
        print("   ❌ FLASK_SECRET_KEY no configurado")
        return False
    
    print("✅ Configuración OAuth verificada")
    return True

def mostrar_resumen_final():
    """Muestra el resumen final del test"""
    print("\n" + "=" * 60)
    print("📊 RESUMEN FINAL")
    print("=" * 60)
    
    print("✅ Base de datos migrada correctamente")
    print("✅ Funciones de Google OAuth funcionando")
    print("✅ Configuración OAuth verificada")
    print("✅ Sistema listo para Google OAuth")
    
    print("\n🚀 PRÓXIMOS PASOS:")
    print("1. Reinicia la aplicación: python app.py")
    print("2. Ve a: http://localhost:5000")
    print("3. Haz clic en 'Iniciar sesión con Google'")
    print("4. ¡Debería funcionar sin errores!")
    
    print("\n🔧 URLs DE DEBUG:")
    print("   - http://localhost:5000/debug/oauth_config")
    print("   - http://localhost:5000/test/oauth_flow")
    print("   - http://localhost:5000/debug/session")

def main():
    """Función principal"""
    print("🎯 TEST FINAL DE OAUTH - ENERVIRGIL")
    print("=" * 60)
    print("Verificando que todo esté listo para Google OAuth")
    
    # Test 1: Base de datos
    if not test_base_datos():
        print("\n❌ FALLO EN TEST DE BASE DE DATOS")
        return
    
    # Test 2: Funciones de Google
    if not test_funciones_google():
        print("\n❌ FALLO EN TEST DE FUNCIONES GOOGLE")
        return
    
    # Test 3: Configuración OAuth
    if not test_configuracion_oauth():
        print("\n❌ FALLO EN TEST DE CONFIGURACIÓN")
        return
    
    # Mostrar resumen
    mostrar_resumen_final()
    
    print("\n🎉 ¡TODOS LOS TESTS PASARON!")
    print("El sistema está completamente listo para Google OAuth")

if __name__ == "__main__":
    main()