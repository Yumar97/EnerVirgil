#!/usr/bin/env python3
"""
Configurador automático de Google OAuth para EnerVirgil
"""

import webbrowser
import time
import os

def abrir_google_console():
    """Abre Google Cloud Console automáticamente"""
    print("🌐 Abriendo Google Cloud Console...")
    webbrowser.open("https://console.cloud.google.com/")
    time.sleep(2)

def crear_proyecto_google():
    """Guía para crear proyecto en Google"""
    print("\n" + "="*60)
    print("📋 PASO 1: CREAR PROYECTO EN GOOGLE CLOUD")
    print("="*60)
    
    print("\n🔗 Se abrirá Google Cloud Console en tu navegador...")
    abrir_google_console()
    
    print("\n📝 Sigue estos pasos en el navegador:")
    print("1. ✅ Inicia sesión con tu cuenta de Google")
    print("2. ✅ Haz clic en 'Seleccionar proyecto' (arriba)")
    print("3. ✅ Haz clic en 'NUEVO PROYECTO'")
    print("4. ✅ Nombre del proyecto: 'EnerVirgil-OAuth'")
    print("5. ✅ Haz clic en 'CREAR'")
    print("6. ✅ Espera a que se cree el proyecto")
    print("7. ✅ Selecciona el proyecto recién creado")
    
    input("\n⏳ Presiona ENTER cuando hayas creado y seleccionado el proyecto...")

def habilitar_apis():
    """Guía para habilitar APIs necesarias"""
    print("\n" + "="*60)
    print("🔌 PASO 2: HABILITAR APIs NECESARIAS")
    print("="*60)
    
    print("\n🌐 Abriendo página de APIs...")
    webbrowser.open("https://console.cloud.google.com/apis/library")
    time.sleep(2)
    
    print("\n📝 Sigue estos pasos:")
    print("1. ✅ Busca 'Google+ API' en la barra de búsqueda")
    print("2. ✅ Haz clic en 'Google+ API'")
    print("3. ✅ Haz clic en 'HABILITAR'")
    print("4. ✅ Espera a que se habilite")
    
    input("\n⏳ Presiona ENTER cuando hayas habilitado la API...")

def configurar_oauth():
    """Guía para configurar OAuth"""
    print("\n" + "="*60)
    print("🔑 PASO 3: CONFIGURAR OAUTH 2.0")
    print("="*60)
    
    print("\n🌐 Abriendo página de credenciales...")
    webbrowser.open("https://console.cloud.google.com/apis/credentials")
    time.sleep(2)
    
    print("\n📝 Sigue estos pasos:")
    print("1. ✅ Haz clic en '+ CREAR CREDENCIALES'")
    print("2. ✅ Selecciona 'ID de cliente de OAuth 2.0'")
    print("3. ✅ Si aparece pantalla de consentimiento, configúrala:")
    print("   - Tipo: Externo")
    print("   - Nombre: EnerVirgil")
    print("   - Email de soporte: tu email")
    print("   - Dominio autorizado: localhost")
    print("4. ✅ Tipo de aplicación: 'Aplicación web'")
    print("5. ✅ Nombre: 'EnerVirgil OAuth Client'")
    print("6. ✅ URIs de origen autorizados:")
    print("   📋 Agregar: http://localhost:5000")
    print("7. ✅ URIs de redirección autorizados:")
    print("   📋 Agregar: http://localhost:5000/auth/google/callback")
    print("8. ✅ Haz clic en 'CREAR'")
    
    input("\n⏳ Presiona ENTER cuando hayas creado las credenciales...")

def obtener_credenciales():
    """Solicita las credenciales al usuario"""
    print("\n" + "="*60)
    print("📋 PASO 4: COPIAR CREDENCIALES")
    print("="*60)
    
    print("\n📝 Ahora deberías ver un popup con tus credenciales:")
    print("1. ✅ Copia el 'ID de cliente'")
    print("2. ✅ Copia el 'Secreto del cliente'")
    print("\n💡 Si cerraste el popup:")
    print("- Haz clic en el ícono de descarga junto a tu credencial")
    print("- O haz clic en el nombre de la credencial para ver los detalles")
    
    print("\n" + "-"*50)
    client_id = input("🔑 Pega aquí tu CLIENT ID: ").strip()
    
    if not client_id:
        print("❌ Error: Client ID es requerido")
        return None, None
    
    client_secret = input("🔐 Pega aquí tu CLIENT SECRET: ").strip()
    
    if not client_secret:
        print("❌ Error: Client Secret es requerido")
        return None, None
    
    return client_id, client_secret

def crear_archivo_env(client_id, client_secret):
    """Crea el archivo .env con las credenciales"""
    print("\n" + "="*60)
    print("💾 PASO 5: GUARDAR CONFIGURACIÓN")
    print("="*60)
    
    env_content = f"""# Configuración de Flask
FLASK_SECRET_KEY=enervirgil_super_secret_key_2024

# Configuración de Google OAuth
GOOGLE_CLIENT_ID={client_id}
GOOGLE_CLIENT_SECRET={client_secret}

# Configuración de Google Custom Search (opcional)
GOOGLE_API_KEY=AIzaSyDswCwJtL0fMsWNc3U8vqRRzqz7dhSr-rI
GOOGLE_CX=b427110346f954ba1

# Configuración de la aplicación
FLASK_ENV=development
FLASK_DEBUG=True"""
    
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ Archivo .env creado exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error creando archivo .env: {e}")
        return False

def crear_script_inicio():
    """Crea script para iniciar la aplicación con variables de entorno"""
    script_content = f"""@echo off
echo ========================================
echo        EnerVirgil con Google OAuth
echo ========================================
echo.

echo 📋 Cargando configuracion...

REM Cargar variables del archivo .env
for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
    if not "%%a"=="" if not "%%a"=="REM" if not "%%a"=="#" (
        set "%%a=%%b"
        echo   ✅ %%a configurado
    )
)

echo.
echo 🚀 Iniciando EnerVirgil...
echo 🌐 La aplicacion estara disponible en: http://localhost:5000
echo 📱 Ahora puedes usar "Iniciar sesion con Google"
echo.

python app.py

echo.
echo 👋 Aplicacion cerrada
pause"""
    
    try:
        with open('iniciar_con_google.bat', 'w', encoding='utf-8') as f:
            f.write(script_content)
        print("✅ Script 'iniciar_con_google.bat' creado")
        return True
    except Exception as e:
        print(f"⚠️ No se pudo crear el script: {e}")
        return False

def verificar_configuracion():
    """Verifica que todo esté configurado correctamente"""
    print("\n" + "="*60)
    print("🔍 VERIFICANDO CONFIGURACIÓN")
    print("="*60)
    
    if not os.path.exists('.env'):
        print("❌ Archivo .env no encontrado")
        return False
    
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'GOOGLE_CLIENT_ID=' in content and 'GOOGLE_CLIENT_SECRET=' in content:
            print("✅ Credenciales de Google configuradas")
        else:
            print("❌ Credenciales de Google no encontradas en .env")
            return False
        
        if 'tu_google_client_id_aqui' not in content:
            print("✅ Client ID configurado correctamente")
        else:
            print("❌ Client ID no configurado")
            return False
        
        if 'tu_google_client_secret_aqui' not in content:
            print("✅ Client Secret configurado correctamente")
        else:
            print("❌ Client Secret no configurado")
            return False
        
        print("✅ Configuración completa y válida")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando configuración: {e}")
        return False

def main():
    """Función principal del configurador"""
    print("🔧 CONFIGURADOR AUTOMÁTICO DE GOOGLE OAUTH")
    print("=" * 60)
    print("Este script te ayudará a configurar Google OAuth paso a paso")
    print("Se abrirán páginas web automáticamente para facilitar el proceso")
    print("=" * 60)
    
    input("\n🚀 Presiona ENTER para comenzar...")
    
    try:
        # Paso 1: Crear proyecto
        crear_proyecto_google()
        
        # Paso 2: Habilitar APIs
        habilitar_apis()
        
        # Paso 3: Configurar OAuth
        configurar_oauth()
        
        # Paso 4: Obtener credenciales
        client_id, client_secret = obtener_credenciales()
        
        if not client_id or not client_secret:
            print("\n❌ Configuración cancelada")
            return False
        
        # Paso 5: Crear archivos de configuración
        if not crear_archivo_env(client_id, client_secret):
            print("\n❌ Error en la configuración")
            return False
        
        crear_script_inicio()
        
        # Verificar configuración
        if verificar_configuracion():
            print("\n" + "="*60)
            print("🎉 ¡CONFIGURACIÓN COMPLETADA EXITOSAMENTE!")
            print("="*60)
            print("\n📋 Próximos pasos:")
            print("1. ✅ Cierra la aplicación actual si está ejecutándose (Ctrl+C)")
            print("2. ✅ Ejecuta: iniciar_con_google.bat")
            print("3. ✅ Ve a: http://localhost:5000")
            print("4. ✅ ¡Ahora puedes usar 'Iniciar sesión con Google'!")
            
            print("\n💡 Notas importantes:")
            print("- El botón de Google aparecerá en la página de login")
            print("- Puedes usar tanto login tradicional como Google")
            print("- Las credenciales están guardadas en .env")
            print("- El archivo .env está en .gitignore por seguridad")
            
            print("\n🔧 Para iniciar la aplicación:")
            print("- Opción 1: Doble clic en 'iniciar_con_google.bat'")
            print("- Opción 2: Ejecutar manualmente 'python app.py'")
            
            return True
        else:
            print("\n❌ Error en la verificación")
            return False
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Configuración cancelada por el usuario")
        return False
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎊 ¡Google OAuth configurado exitosamente!")
        input("\nPresiona ENTER para salir...")
    else:
        print("\n😞 Configuración no completada")
        print("💡 Puedes intentar de nuevo ejecutando este script")
        input("\nPresiona ENTER para salir...")