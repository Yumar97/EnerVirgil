"""
Módulo para cargar variables de entorno desde archivo .env
"""

import os

def load_env_file():
    """Carga variables de entorno desde archivo .env"""
    env_path = '.env'
    
    if not os.path.exists(env_path):
        print("⚠️ Archivo .env no encontrado")
        return False
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    os.environ[key] = value
        
        print("✅ Variables de entorno cargadas desde .env")
        return True
        
    except Exception as e:
        print(f"❌ Error cargando .env: {e}")
        return False

# Cargar automáticamente al importar
load_env_file()