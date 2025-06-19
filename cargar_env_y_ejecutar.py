#!/usr/bin/env python3
"""
Script para cargar variables de entorno desde .env y ejecutar la aplicación
"""

import os
import subprocess
import sys

def cargar_variables_env():
    """Carga variables de entorno desde archivo .env"""
    if not os.path.exists('.env'):
        print("❌ Archivo .env no encontrado")
        return False
    
    print("📋 Cargando variables de entorno...")
    
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
                    print(f"  ✅ {key} configurado")
        
        print("✅ Variables de entorno cargadas exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error cargando variables: {e}")
        return False

def verificar_google_oauth():
    """Verifica que Google OAuth esté configurado"""
    client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    
    if client_id and client_id != 'tu_google_client_id_aqui':
        if client_secret and client_secret != 'tu_google_client_secret_aqui':
            print("✅ Google OAuth configurado correctamente")
            return True
    
    print("⚠️ Google OAuth no configurado")
    return False

def main():
    print("🚀 EnerVirgil - Iniciando con Google OAuth")
    print("=" * 50)
    
    # Cargar variables de entorno
    if not cargar_variables_env():
        input("Presiona ENTER para salir...")
        return
    
    # Verificar configuración
    google_enabled = verificar_google_oauth()
    
    print(f"\n🌐 Google OAuth: {'✅ Habilitado' if google_enabled else '❌ Deshabilitado'}")
    print("🔗 URL de la aplicación: http://localhost:5000")
    
    if google_enabled:
        print("📱 Funciones disponibles:")
        print("  - Login tradicional (usuario/contraseña)")
        print("  - Login con Google")
    else:
        print("📱 Solo login tradicional disponible")
    
    print("\n🚀 Iniciando aplicación...")
    print("-" * 50)
    
    try:
        # Ejecutar la aplicación
        subprocess.run([sys.executable, 'app.py'])
    except KeyboardInterrupt:
        print("\n\n⏹️ Aplicación detenida por el usuario")
    except Exception as e:
        print(f"\n❌ Error ejecutando la aplicación: {e}")
    
    print("\n👋 Aplicación cerrada")

if __name__ == "__main__":
    main()