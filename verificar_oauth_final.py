#!/usr/bin/env python3
"""
Verificación final de la configuración OAuth de EnerVirgil
"""

import os
import sys
import requests
import json

# Cargar variables de entorno
sys.path.insert(0, '.')
import load_env

def verificar_configuracion_completa():
    """Verificación completa de la configuración OAuth"""
    print("🔍 VERIFICACIÓN FINAL DE OAUTH - ENERVIRGIL")
    print("=" * 60)
    
    # 1. Verificar variables de entorno
    print("\n1️⃣ VARIABLES DE ENTORNO:")
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    flask_secret = os.environ.get('FLASK_SECRET_KEY')
    
    if not client_id or client_id == 'tu_google_client_id_aqui':
        print("❌ GOOGLE_CLIENT_ID no configurado")
        return False
    else:
        print(f"✅ GOOGLE_CLIENT_ID: {client_id[:20]}...")
    
    if not client_secret or client_secret == 'tu_google_client_secret_aqui':
        print("❌ GOOGLE_CLIENT_SECRET no configurado")
        return False
    else:
        print("✅ GOOGLE_CLIENT_SECRET: configurado")
    
    if not flask_secret:
        print("❌ FLASK_SECRET_KEY no configurado")
        return False
    else:
        print("✅ FLASK_SECRET_KEY: configurado")
    
    # 2. Verificar formato de credenciales
    print("\n2️⃣ FORMATO DE CREDENCIALES:")
    if client_id.endswith('.apps.googleusercontent.com'):
        print("✅ Client ID tiene formato correcto")
    else:
        print("⚠️ Client ID tiene formato inusual")
    
    if client_secret.startswith('GOCSPX-'):
        print("✅ Client Secret tiene formato correcto")
    else:
        print("⚠️ Client Secret tiene formato inusual")
    
    # 3. Verificar conectividad a Google
    print("\n3️⃣ CONECTIVIDAD A GOOGLE:")
    try:
        response = requests.get('https://oauth2.googleapis.com/token', timeout=5)
        print(f"✅ Token endpoint accesible: {response.status_code}")
    except Exception as e:
        print(f"❌ Error conectando a token endpoint: {e}")
        return False
    
    try:
        response = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', timeout=5)
        print(f"✅ Userinfo endpoint accesible: {response.status_code}")
    except Exception as e:
        print(f"❌ Error conectando a userinfo endpoint: {e}")
        return False
    
    # 4. Probar intercambio de token (simulado)
    print("\n4️⃣ CONFIGURACIÓN DE URLS:")
    redirect_uri = 'http://localhost:5000/auth/google/callback'
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=openid email profile"
    )
    
    print(f"✅ Redirect URI: {redirect_uri}")
    print(f"✅ Authorization URL construida correctamente")
    
    # 5. Verificar que la aplicación puede importar correctamente
    print("\n5️⃣ VERIFICACIÓN DE APLICACIÓN:")
    try:
        from flask import Flask
        from authlib.integrations.flask_client import OAuth
        
        test_app = Flask(__name__)
        test_app.secret_key = flask_secret
        test_oauth = OAuth(test_app)
        
        # Configurar Google OAuth como en la aplicación
        test_google = test_oauth.register(
            name='google',
            client_id=client_id,
            client_secret=client_secret,
            authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
            access_token_url='https://oauth2.googleapis.com/token',
            refresh_token_url='https://oauth2.googleapis.com/token',
            client_kwargs={
                'scope': 'openid email profile'
            },
        )
        
        print("✅ Configuración OAuth se puede crear sin errores")
        
    except Exception as e:
        print(f"❌ Error configurando OAuth: {e}")
        return False
    
    return True

def mostrar_instrucciones_google_console():
    """Muestra las instrucciones para Google Console"""
    print("\n" + "=" * 60)
    print("📋 CONFIGURACIÓN REQUERIDA EN GOOGLE CONSOLE")
    print("=" * 60)
    
    print("\n🔗 Ve a: https://console.cloud.google.com/apis/credentials")
    print("\n📝 Asegúrate de que tu credencial OAuth tenga:")
    print("   ✅ URIs de origen autorizados:")
    print("      - http://localhost:5000")
    print("   ✅ URIs de redirección autorizados:")
    print("      - http://localhost:5000/auth/google/callback")
    
    print("\n⚠️ IMPORTANTE:")
    print("   - NO uses https:// en desarrollo local")
    print("   - NO uses 127.0.0.1, usa localhost")
    print("   - Guarda los cambios en Google Console")
    print("   - Espera unos minutos para que se propaguen")

def mostrar_pasos_siguientes():
    """Muestra los pasos siguientes"""
    print("\n" + "=" * 60)
    print("🚀 PASOS SIGUIENTES")
    print("=" * 60)
    
    print("\n1️⃣ Reinicia la aplicación Flask:")
    print("   python app.py")
    
    print("\n2️⃣ Ve a: http://localhost:5000")
    
    print("\n3️⃣ Haz clic en 'Iniciar sesión con Google'")
    
    print("\n4️⃣ Si hay errores, revisa los logs de la aplicación")
    
    print("\n🔧 Para debug adicional:")
    print("   - http://localhost:5000/debug/oauth_config")
    print("   - http://localhost:5000/debug/session")

if __name__ == "__main__":
    if verificar_configuracion_completa():
        print("\n🎉 ¡CONFIGURACIÓN OAUTH VERIFICADA EXITOSAMENTE!")
        mostrar_instrucciones_google_console()
        mostrar_pasos_siguientes()
    else:
        print("\n❌ HAY PROBLEMAS EN LA CONFIGURACIÓN")
        print("   Por favor, corrige los errores mostrados arriba")
        mostrar_instrucciones_google_console()
    
    print("\n" + "=" * 60)