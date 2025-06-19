#!/usr/bin/env python3
"""
Script de verificación para el despliegue de EnerVirgil
Verifica que todos los archivos y configuraciones estén listos
"""

import os
import sys
from pathlib import Path

def verificar_archivo(archivo, descripcion):
    """Verifica si un archivo existe"""
    if os.path.exists(archivo):
        print(f"✅ {descripcion}: {archivo}")
        return True
    else:
        print(f"❌ {descripcion}: {archivo} - NO ENCONTRADO")
        return False

def verificar_contenido_archivo(archivo, contenido_requerido, descripcion):
    """Verifica si un archivo contiene cierto contenido"""
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
            if contenido_requerido in contenido:
                print(f"✅ {descripcion}: Configurado correctamente")
                return True
            else:
                print(f"⚠️  {descripcion}: Puede necesitar configuración")
                return False
    except FileNotFoundError:
        print(f"❌ {descripcion}: Archivo no encontrado")
        return False

def main():
    print("🔍 VERIFICACIÓN DE DESPLIEGUE - EnerVirgil")
    print("=" * 50)
    
    errores = 0
    advertencias = 0
    
    # Verificar archivos esenciales
    print("\n📁 ARCHIVOS ESENCIALES:")
    archivos_esenciales = [
        ("app.py", "Aplicación principal"),
        ("requirements.txt", "Dependencias Python"),
        ("Procfile", "Comando de inicio"),
        ("gunicorn.conf.py", "Configuración del servidor"),
        ("runtime.txt", "Versión de Python"),
        (".gitignore", "Archivos a ignorar"),
    ]
    
    for archivo, desc in archivos_esenciales:
        if not verificar_archivo(archivo, desc):
            errores += 1
    
    # Verificar templates
    print("\n📧 TEMPLATES DE CORREO:")
    templates = [
        ("templates/email_bienvenida.html", "Template correo nuevo usuario"),
        ("templates/email_bienvenida_vuelta.html", "Template correo usuario recurrente"),
        ("templates/test_email.html", "Template prueba de correos"),
    ]
    
    for template, desc in templates:
        if not verificar_archivo(template, desc):
            errores += 1
    
    # Verificar configuraciones en archivos
    print("\n⚙️  CONFIGURACIONES:")
    
    # Verificar requirements.txt
    if not verificar_contenido_archivo("requirements.txt", "gunicorn", "Gunicorn en requirements.txt"):
        advertencias += 1
    
    # Verificar app.py para configuración de producción
    if not verificar_contenido_archivo("app.py", "is_production", "Configuración de producción en app.py"):
        advertencias += 1
    
    # Verificar templates para URLs dinámicas
    if not verificar_contenido_archivo("templates/email_bienvenida.html", "base_url", "URLs dinámicas en template"):
        advertencias += 1
    
    # Verificar estructura de directorios
    print("\n📂 ESTRUCTURA DE DIRECTORIOS:")
    directorios = ["templates", "static"]
    for directorio in directorios:
        if os.path.isdir(directorio):
            print(f"✅ Directorio: {directorio}")
        else:
            print(f"⚠️  Directorio: {directorio} - No encontrado (puede ser opcional)")
            advertencias += 1
    
    # Verificar archivos de configuración opcionales
    print("\n🔧 ARCHIVOS DE CONFIGURACIÓN OPCIONALES:")
    opcionales = [
        (".env.example", "Ejemplo de variables de entorno"),
        (".env.production", "Template de producción"),
        ("render.yaml", "Configuración de Render"),
        ("GUIA_DESPLIEGUE.md", "Guía de despliegue"),
    ]
    
    for archivo, desc in opcionales:
        verificar_archivo(archivo, desc)
    
    # Verificar variables de entorno críticas
    print("\n🔐 VARIABLES DE ENTORNO CRÍTICAS:")
    variables_criticas = [
        "FLASK_SECRET_KEY",
        "MAIL_USERNAME", 
        "MAIL_PASSWORD",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET"
    ]
    
    print("⚠️  Recuerda configurar estas variables en tu plataforma de despliegue:")
    for var in variables_criticas:
        print(f"   - {var}")
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE VERIFICACIÓN:")
    print(f"✅ Archivos correctos: {len(archivos_esenciales + templates) - errores}")
    print(f"❌ Errores críticos: {errores}")
    print(f"⚠️  Advertencias: {advertencias}")
    
    if errores == 0:
        print("\n🎉 ¡LISTO PARA DESPLIEGUE!")
        print("Tu aplicación EnerVirgil está preparada para subir a la web.")
        print("\nPróximos pasos:")
        print("1. Sube el código a GitHub")
        print("2. Crea un servicio en Render/Railway/Heroku")
        print("3. Configura las variables de entorno")
        print("4. ¡Disfruta tu app en la web!")
    else:
        print(f"\n🚨 ERRORES ENCONTRADOS: {errores}")
        print("Por favor, corrige los errores antes de desplegar.")
        return 1
    
    if advertencias > 0:
        print(f"\n⚠️  ADVERTENCIAS: {advertencias}")
        print("Revisa las advertencias para un despliegue óptimo.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())