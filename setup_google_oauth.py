#!/usr/bin/env python3
"""
Script para configurar Google OAuth paso a paso
"""

import os
import webbrowser

def setup_google_oauth():
    print("🔧 Configuración de Google OAuth para EnerVirgil")
    print("=" * 50)
    
    print("\n📋 PASO 1: Crear proyecto en Google Cloud Console")
    print("1. Ve a: https://console.cloud.google.com/")
    print("2. Crea un nuevo proyecto o selecciona uno existente")
    print("3. Habilita la API de Google+ (Google People API)")
    
    input("\nPresiona Enter cuando hayas completado el Paso 1...")
    
    print("\n🔑 PASO 2: Configurar OAuth 2.0")
    print("1. Ve a 'APIs y servicios' > 'Credenciales'")
    print("2. Haz clic en 'Crear credenciales' > 'ID de cliente de OAuth 2.0'")
    print("3. Selecciona 'Aplicación web'")
    print("4. Configura las URIs:")
    print("   - URIs de origen autorizados: http://localhost:5000")
    print("   - URIs de redirección autorizados: http://localhost:5000/auth/google/callback")
    
    input("\nPresiona Enter cuando hayas completado el Paso 2...")
    
    print("\n📝 PASO 3: Obtener credenciales")
    client_id = input("Ingresa tu Google Client ID: ").strip()
    client_secret = input("Ingresa tu Google Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("❌ Error: Debes proporcionar ambas credenciales")
        return False
    
    print("\n💾 PASO 4: Guardar configuración")
    
    # Crear archivo .env
    env_content = f"""# Configuración de Flask
FLASK_SECRET_KEY=tu_clave_secreta_muy_segura_aqui

# Configuración de Google OAuth
GOOGLE_CLIENT_ID={client_id}
GOOGLE_CLIENT_SECRET={client_secret}

# Configuración de Google Custom Search (opcional)
GOOGLE_API_KEY=tu_google_api_key_aqui
GOOGLE_CX=tu_google_cx_aqui

# Configuración de la aplicación
FLASK_ENV=development
FLASK_DEBUG=True"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Archivo .env creado exitosamente")
    except Exception as e:
        print(f"❌ Error creando archivo .env: {e}")
        return False
    
    # Crear script para cargar variables de entorno
    load_env_script = """@echo off
echo Cargando variables de entorno...
for /f "delims=" %%x in (.env) do (
    set "%%x"
)
echo Variables cargadas. Iniciando aplicacion...
python app.py
pause"""
    
    try:
        with open('run_with_env.bat', 'w') as f:
            f.write(load_env_script)
        print("✅ Script run_with_env.bat creado")
    except Exception as e:
        print(f"⚠️ No se pudo crear run_with_env.bat: {e}")
    
    print("\n🎉 ¡Configuración completada!")
    print("\n📋 Próximos pasos:")
    print("1. Cierra la aplicación actual (Ctrl+C)")
    print("2. Ejecuta: run_with_env.bat")
    print("   O manualmente:")
    print("   - set GOOGLE_CLIENT_ID=" + client_id)
    print("   - set GOOGLE_CLIENT_SECRET=" + client_secret)
    print("   - python app.py")
    print("\n✨ Después podrás usar 'Iniciar sesión con Google'")
    
    return True

def quick_setup():
    """Configuración rápida para testing"""
    print("\n🚀 CONFIGURACIÓN RÁPIDA (Solo para testing)")
    print("Si ya tienes las credenciales, puedes configurarlas directamente:")
    
    client_id = input("\nGoogle Client ID (o Enter para omitir): ").strip()
    if not client_id:
        return False
    
    client_secret = input("Google Client Secret: ").strip()
    if not client_secret:
        return False
    
    # Configurar variables de entorno para la sesión actual
    os.environ['GOOGLE_CLIENT_ID'] = client_id
    os.environ['GOOGLE_CLIENT_SECRET'] = client_secret
    
    print("✅ Variables configuradas para esta sesión")
    print("⚠️ Nota: Estas variables se perderán al cerrar la terminal")
    print("💡 Para configuración permanente, usa la opción completa")
    
    return True

if __name__ == "__main__":
    print("Selecciona una opción:")
    print("1. Configuración completa (recomendado)")
    print("2. Configuración rápida (solo esta sesión)")
    print("3. Abrir documentación")
    
    choice = input("\nOpción (1-3): ").strip()
    
    if choice == "1":
        setup_google_oauth()
    elif choice == "2":
        if quick_setup():
            print("\n🔄 Reinicia la aplicación para aplicar los cambios")
    elif choice == "3":
        webbrowser.open("https://console.cloud.google.com/")
        print("📖 Documentación abierta en el navegador")
    else:
        print("❌ Opción inválida")