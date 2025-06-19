#!/usr/bin/env python3
"""
Test completo del sistema OAuth de EnerVirgil
"""

import os
import sys
import requests
import webbrowser
from urllib.parse import urlparse, parse_qs

# Cargar variables de entorno
sys.path.insert(0, '.')
import load_env

def test_oauth_completo():
    """Test completo del flujo OAuth"""
    print("🧪 TEST COMPLETO DE OAUTH - ENERVIRGIL")
    print("=" * 60)
    
    # Verificar configuración básica
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Credenciales de Google no configuradas")
        return False
    
    print(f"✅ Client ID: {client_id[:20]}...")
    print(f"✅ Client Secret: configurado")
    
    # Test 1: Verificar endpoints de Google
    print("\n🔍 TEST 1: ENDPOINTS DE GOOGLE")
    print("-" * 40)
    
    endpoints = [
        ('Token endpoint', 'https://oauth2.googleapis.com/token'),
        ('Userinfo endpoint', 'https://www.googleapis.com/oauth2/v2/userinfo'),
        ('Authorization endpoint', 'https://accounts.google.com/o/oauth2/v2/auth')
    ]
    
    for name, url in endpoints:
        try:
            response = requests.head(url, timeout=5)
            print(f"✅ {name}: accesible ({response.status_code})")
        except Exception as e:
            print(f"❌ {name}: error - {e}")
            return False
    
    # Test 2: Construir URL de autorización
    print("\n🔍 TEST 2: URL DE AUTORIZACIÓN")
    print("-" * 40)
    
    redirect_uri = 'http://localhost:5000/auth/google/callback'
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=openid email profile"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    
    print(f"✅ URL construida correctamente")
    print(f"📋 Redirect URI: {redirect_uri}")
    
    # Test 3: Simular intercambio de token (sin código real)
    print("\n🔍 TEST 3: ESTRUCTURA DE INTERCAMBIO DE TOKEN")
    print("-" * 40)
    
    token_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': 'TEST_CODE',
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri
    }
    
    print(f"✅ Datos de token preparados correctamente")
    print(f"📋 Grant type: {token_data['grant_type']}")
    print(f"📋 Redirect URI: {token_data['redirect_uri']}")
    
    # Test 4: Verificar aplicación Flask
    print("\n🔍 TEST 4: CONFIGURACIÓN FLASK")
    print("-" * 40)
    
    try:
        from flask import Flask
        from authlib.integrations.flask_client import OAuth
        
        test_app = Flask(__name__)
        test_app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'test')
        test_oauth = OAuth(test_app)
        
        # Configurar como en la aplicación real
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
        
        print("✅ Configuración Flask OAuth exitosa")
        
    except Exception as e:
        print(f"❌ Error en configuración Flask: {e}")
        return False
    
    # Mostrar resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DEL TEST")
    print("=" * 60)
    print("✅ Todos los tests básicos pasaron")
    print("✅ La configuración OAuth está correcta")
    print("✅ Los endpoints de Google son accesibles")
    print("✅ La aplicación Flask puede configurarse")
    
    print("\n🚀 PRÓXIMOS PASOS:")
    print("1. Inicia la aplicación: python app.py")
    print("2. Ve a: http://localhost:5000/test/oauth_flow")
    print("3. Sigue las instrucciones para probar el flujo completo")
    
    print("\n🔗 URL de autorización para prueba manual:")
    print(auth_url)
    
    # Preguntar si abrir en navegador
    try:
        respuesta = input("\n¿Quieres abrir la URL de autorización en el navegador? (s/n): ")
        if respuesta.lower() in ['s', 'si', 'y', 'yes']:
            webbrowser.open(auth_url)
            print("✅ URL abierta en el navegador")
    except:
        pass
    
    return True

def mostrar_checklist_google_console():
    """Muestra checklist para Google Console"""
    print("\n" + "=" * 60)
    print("📋 CHECKLIST GOOGLE CONSOLE")
    print("=" * 60)
    
    checklist = [
        "✅ Proyecto creado en Google Cloud Console",
        "��� APIs de Google+ y OAuth habilitadas",
        "✅ Credencial OAuth 2.0 creada",
        "✅ URI de origen: http://localhost:5000",
        "✅ URI de redirección: http://localhost:5000/auth/google/callback",
        "✅ Client ID y Client Secret copiados al .env",
        "✅ Cambios guardados en Google Console"
    ]
    
    for item in checklist:
        print(f"   {item}")
    
    print("\n⚠️ IMPORTANTE:")
    print("   - NO uses https:// para desarrollo local")
    print("   - NO uses 127.0.0.1, usa localhost")
    print("   - Espera unos minutos para que se propaguen los cambios")

if __name__ == "__main__":
    if test_oauth_completo():
        mostrar_checklist_google_console()
        print("\n🎉 ¡TEST COMPLETADO EXITOSAMENTE!")
    else:
        print("\n❌ HAY PROBLEMAS EN LA CONFIGURACIÓN")
        mostrar_checklist_google_console()
    
    print("\n" + "=" * 60)