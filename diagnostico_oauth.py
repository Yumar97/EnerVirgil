#!/usr/bin/env python3
"""
Diagnóstico completo del sistema OAuth de EnerVirgil
"""

import os
import sys
import requests
import json
from urllib.parse import urlparse, parse_qs

# Cargar variables de entorno
sys.path.insert(0, '.')
import load_env

def verificar_variables_entorno():
    """Verifica las variables de entorno"""
    print("🔍 VERIFICANDO VARIABLES DE ENTORNO")
    print("=" * 50)
    
    variables = {
        'FLASK_SECRET_KEY': os.environ.get('FLASK_SECRET_KEY'),
        'GOOGLE_CLIENT_ID': os.environ.get('GOOGLE_CLIENT_ID'),
        'GOOGLE_CLIENT_SECRET': os.environ.get('GOOGLE_CLIENT_SECRET'),
    }
    
    for var, value in variables.items():
        if value:
            if var == 'GOOGLE_CLIENT_ID':
                print(f"✅ {var}: {value[:20]}...")
            elif var == 'GOOGLE_CLIENT_SECRET':
                print(f"✅ {var}: {'*' * 20}")
            else:
                print(f"✅ {var}: SET")
        else:
            print(f"❌ {var}: NO SET")
    
    return all(variables.values())

def verificar_google_oauth_config():
    """Verifica la configuración de Google OAuth"""
    print("\n🔍 VERIFICANDO CONFIGURACIÓN DE GOOGLE OAUTH")
    print("=" * 50)
    
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Credenciales de Google no configuradas")
        return False
    
    # Verificar formato del Client ID
    if not client_id.endswith('.apps.googleusercontent.com'):
        print(f"⚠️ Client ID tiene formato inusual: {client_id[:30]}...")
    else:
        print(f"✅ Client ID tiene formato correcto: {client_id[:30]}...")
    
    # Verificar formato del Client Secret
    if not client_secret.startswith('GOCSPX-'):
        print(f"⚠️ Client Secret tiene formato inusual")
    else:
        print(f"✅ Client Secret tiene formato correcto")
    
    return True

def verificar_metadata_google():
    """Verifica que podemos acceder a la metadata de Google"""
    print("\n🔍 VERIFICANDO METADATA DE GOOGLE")
    print("=" * 50)
    
    try:
        response = requests.get('https://accounts.google.com/.well-known/openid_configuration', timeout=10)
        if response.status_code == 200:
            metadata = response.json()
            print("✅ Metadata de Google accesible")
            print(f"✅ Authorization endpoint: {metadata.get('authorization_endpoint')}")
            print(f"✅ Token endpoint: {metadata.get('token_endpoint')}")
            print(f"✅ Userinfo endpoint: {metadata.get('userinfo_endpoint')}")
            print(f"✅ JWKS URI: {metadata.get('jwks_uri')}")
            return True
        else:
            print(f"❌ Error accediendo a metadata: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def simular_flujo_oauth():
    """Simula el flujo OAuth para detectar problemas"""
    print("\n🔍 SIMULANDO FLUJO OAUTH")
    print("=" * 50)
    
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    redirect_uri = 'http://localhost:5000/auth/google/callback'
    
    # Construir URL de autorización
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=openid email profile"
        f"&state=test_state_123"
    )
    
    print(f"✅ URL de autorización construida:")
    print(f"   {auth_url[:100]}...")
    
    # Verificar que la URL es válida
    try:
        response = requests.head(auth_url, timeout=10, allow_redirects=False)
        if response.status_code in [200, 302, 400]:  # 400 es esperado sin parámetros válidos
            print("✅ URL de autorización es accesible")
        else:
            print(f"⚠️ Respuesta inesperada: {response.status_code}")
    except Exception as e:
        print(f"❌ Error verificando URL: {e}")
    
    return auth_url

def verificar_authlib():
    """Verifica la instalación y configuración de Authlib"""
    print("\n🔍 VERIFICANDO AUTHLIB")
    print("=" * 50)
    
    try:
        import authlib
        print(f"✅ Authlib instalado: versión {authlib.__version__}")
        
        from authlib.integrations.flask_client import OAuth
        print("✅ OAuth de Flask disponible")
        
        # Verificar que podemos crear una instancia
        from flask import Flask
        test_app = Flask(__name__)
        test_app.secret_key = 'test'
        oauth = OAuth(test_app)
        print("✅ OAuth se puede instanciar")
        
        return True
    except ImportError as e:
        print(f"❌ Error importando Authlib: {e}")
        return False
    except Exception as e:
        print(f"❌ Error configurando Authlib: {e}")
        return False

def verificar_flask_session():
    """Verifica la configuración de sesiones de Flask"""
    print("\n🔍 VERIFICANDO CONFIGURACIÓN DE FLASK")
    print("=" * 50)
    
    try:
        from flask import Flask
        test_app = Flask(__name__)
        
        # Verificar secret key
        secret_key = os.environ.get('FLASK_SECRET_KEY')
        if secret_key:
            test_app.secret_key = secret_key
            print(f"✅ Secret key configurado: {len(secret_key)} caracteres")
        else:
            print("❌ Secret key no configurado")
            return False
        
        # Verificar configuración de cookies
        test_app.config['SESSION_COOKIE_SECURE'] = False
        test_app.config['SESSION_COOKIE_HTTPONLY'] = True
        test_app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        print("✅ Configuración de cookies establecida")
        
        return True
    except Exception as e:
        print(f"❌ Error configurando Flask: {e}")
        return False

def verificar_conectividad():
    """Verifica la conectividad a servicios de Google"""
    print("\n🔍 VERIFICANDO CONECTIVIDAD")
    print("=" * 50)
    
    urls_test = [
        'https://accounts.google.com',
        'https://oauth2.googleapis.com',
        'https://www.googleapis.com',
    ]
    
    for url in urls_test:
        try:
            response = requests.get(url, timeout=5)
            print(f"✅ {url}: {response.status_code}")
        except Exception as e:
            print(f"❌ {url}: {e}")

def generar_reporte():
    """Genera un reporte completo del diagnóstico"""
    print("\n" + "=" * 60)
    print("📋 REPORTE DE DIAGNÓSTICO OAUTH")
    print("=" * 60)
    
    resultados = []
    
    # Ejecutar todas las verificaciones
    resultados.append(("Variables de entorno", verificar_variables_entorno()))
    resultados.append(("Configuración Google OAuth", verificar_google_oauth_config()))
    resultados.append(("Metadata de Google", verificar_metadata_google()))
    resultados.append(("Authlib", verificar_authlib()))
    resultados.append(("Flask Session", verificar_flask_session()))
    
    # Verificaciones adicionales
    verificar_conectividad()
    auth_url = simular_flujo_oauth()
    
    # Mostrar resumen
    print("\n📊 RESUMEN:")
    for nombre, resultado in resultados:
        estado = "✅ OK" if resultado else "❌ FALLO"
        print(f"   {nombre}: {estado}")
    
    # Recomendaciones
    print("\n💡 RECOMENDACIONES:")
    
    fallos = [nombre for nombre, resultado in resultados if not resultado]
    if fallos:
        print("   🔧 Corregir los siguientes problemas:")
        for fallo in fallos:
            print(f"      - {fallo}")
    else:
        print("   ✅ Todas las verificaciones básicas pasaron")
        print("   🔍 El problema puede estar en:")
        print("      - Configuración incorrecta en Google Console")
        print("      - URLs de redirección no coinciden")
        print("      - Problema de timing en el flujo OAuth")
    
    print("\n🔗 URL de autorización para pruebas manuales:")
    print(f"   {auth_url}")
    
    print("\n📝 PASOS SIGUIENTES:")
    print("   1. Corregir cualquier fallo mostrado arriba")
    print("   2. Verificar configuración en Google Console")
    print("   3. Probar la URL de autorización manualmente")
    print("   4. Revisar logs detallados de la aplicación")

if __name__ == "__main__":
    print("🚀 DIAGNÓSTICO COMPLETO DE OAUTH - ENERVIRGIL")
    print("=" * 60)
    generar_reporte()
    print("\n✅ Diagnóstico completado")