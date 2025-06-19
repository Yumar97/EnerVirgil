#!/usr/bin/env python3
"""
Script para configurar el correo electrónico en EnerVirgil
"""

import os
import sys
import webbrowser

# Cargar variables de entorno
sys.path.insert(0, '.')
import load_env

def mostrar_instrucciones_gmail():
    """Muestra las instrucciones para configurar Gmail"""
    print("📧 CONFIGURACIÓN DE CORREO GMAIL")
    print("=" * 60)
    
    print("\n🔐 PASO 1: HABILITAR VERIFICACIÓN EN 2 PASOS")
    print("-" * 50)
    print("1. Ve a tu cuenta de Google: https://myaccount.google.com")
    print("2. En el panel izquierdo, haz clic en 'Seguridad'")
    print("3. En 'Iniciar sesión en Google', haz clic en 'Verificación en 2 pasos'")
    print("4. Sigue las instrucciones para configurar la verificación en 2 pasos")
    
    print("\n🔑 PASO 2: GENERAR CONTRASEÑA DE APLICACIÓN")
    print("-" * 50)
    print("1. Ve a: https://myaccount.google.com/apppasswords")
    print("2. Selecciona 'Correo' y 'Otro (nombre personalizado)'")
    print("3. Escribe 'EnerVirgil' como nombre")
    print("4. Haz clic en 'Generar'")
    print("5. Copia la contraseña de 16 caracteres que aparece")
    
    print("\n⚠️ IMPORTANTE:")
    print("- La contraseña de aplicación es diferente a tu contraseña de Gmail")
    print("- Solo se muestra una vez, así que cópiala inmediatamente")
    print("- Guárdala en un lugar seguro")

def configurar_variables_correo():
    """Configura las variables de correo en el archivo .env"""
    print("\n⚙️ CONFIGURACIÓN DE VARIABLES")
    print("=" * 60)
    
    try:
        # Leer archivo .env actual
        env_path = '.env'
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("📋 Configuración actual:")
        mail_username = os.environ.get('MAIL_USERNAME', 'tu_email@gmail.com')
        mail_password = os.environ.get('MAIL_PASSWORD', 'tu_app_password_aqui')
        mail_sender = os.environ.get('MAIL_DEFAULT_SENDER', 'tu_email@gmail.com')
        
        print(f"   MAIL_USERNAME: {mail_username}")
        print(f"   MAIL_PASSWORD: {'*' * len(mail_password) if mail_password != 'tu_app_password_aqui' else 'NO CONFIGURADO'}")
        print(f"   MAIL_DEFAULT_SENDER: {mail_sender}")
        
        # Solicitar nueva configuración
        print("\n📝 Ingresa la nueva configuración:")
        
        nuevo_email = input("Email de Gmail: ").strip()
        if not nuevo_email or '@gmail.com' not in nuevo_email:
            print("❌ Debes ingresar un email válido de Gmail")
            return False
        
        nueva_password = input("Contraseña de aplicación (16 caracteres): ").strip()
        if not nueva_password or len(nueva_password) != 16:
            print("❌ La contraseña de aplicación debe tener exactamente 16 caracteres")
            return False
        
        # Actualizar archivo .env
        lines = content.split('\n')
        updated_lines = []
        
        variables_actualizadas = {
            'MAIL_USERNAME': nuevo_email,
            'MAIL_PASSWORD': nueva_password,
            'MAIL_DEFAULT_SENDER': nuevo_email
        }
        
        for line in lines:
            updated = False
            for var, value in variables_actualizadas.items():
                if line.startswith(f'{var}='):
                    updated_lines.append(f'{var}={value}')
                    updated = True
                    break
            if not updated:
                updated_lines.append(line)
        
        # Escribir archivo actualizado
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(updated_lines))
        
        print("\n✅ Configuración actualizada exitosamente")
        print(f"   Email configurado: {nuevo_email}")
        print(f"   Contraseña: {'*' * 16}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configurando variables: {e}")
        return False

def probar_configuracion():
    """Prueba la configuración de correo"""
    print("\n🧪 PROBANDO CONFIGURACIÓN")
    print("=" * 60)
    
    try:
        # Recargar variables de entorno
        import importlib
        importlib.reload(load_env)
        
        # Importar funciones de la aplicación
        from app import verificar_configuracion_correo, enviar_correo_test
        
        # Verificar configuración
        if not verificar_configuracion_correo():
            print("❌ Configuración de correo incompleta")
            return False
        
        print("✅ Configuración de correo verificada")
        
        # Solicitar email de prueba
        email_prueba = input("\nIngresa un email para enviar correo de prueba: ").strip()
        if not email_prueba:
            print("ℹ️ Saltando prueba de envío")
            return True
        
        print(f"📤 Enviando correo de prueba a {email_prueba}...")
        
        success, message = enviar_correo_test(email_prueba)
        
        if success:
            print("✅ Correo de prueba enviado exitosamente")
            print("📧 Revisa tu bandeja de entrada")
            return True
        else:
            print(f"❌ Error enviando correo: {message}")
            return False
        
    except Exception as e:
        print(f"❌ Error probando configuración: {e}")
        return False

def mostrar_urls_debug():
    """Muestra las URLs de debug disponibles"""
    print("\n🔧 URLS DE DEBUG DISPONIBLES")
    print("=" * 60)
    
    urls = [
        ("Configuración de correo", "http://localhost:5000/debug/mail_config"),
        ("Configuración OAuth", "http://localhost:5000/debug/oauth_config"),
        ("Estado de sesión", "http://localhost:5000/debug/session"),
        ("Flujo OAuth", "http://localhost:5000/test/oauth_flow")
    ]
    
    for nombre, url in urls:
        print(f"   {nombre}: {url}")
    
    print("\n📝 PARA PROBAR CORREOS (después de hacer login):")
    print("   POST /test/send_email - Enviar correo de prueba")
    print("   POST /test/welcome_email - Enviar correo de bienvenida")

def main():
    """Función principal"""
    print("📧 CONFIGURADOR DE CORREO - ENERVIRGIL")
    print("=" * 60)
    print("Este script te ayudará a configurar el envío de correos de bienvenida")
    
    # Mostrar instrucciones
    mostrar_instrucciones_gmail()
    
    # Preguntar si abrir URLs
    try:
        respuesta = input("\n¿Abrir URLs de configuración de Gmail en el navegador? (s/n): ")
        if respuesta.lower() in ['s', 'si', 'y', 'yes']:
            webbrowser.open('https://myaccount.google.com/security')
            webbrowser.open('https://myaccount.google.com/apppasswords')
            print("✅ URLs abiertas en el navegador")
    except:
        pass
    
    # Configurar variables
    print("\n" + "=" * 60)
    respuesta = input("¿Configurar variables de correo ahora? (s/n): ")
    if respuesta.lower() in ['s', 'si', 'y', 'yes']:
        if configurar_variables_correo():
            # Probar configuración
            print("\n" + "=" * 60)
            respuesta = input("¿Probar la configuración de correo? (s/n): ")
            if respuesta.lower() in ['s', 'si', 'y', 'yes']:
                probar_configuracion()
    
    # Mostrar URLs de debug
    mostrar_urls_debug()
    
    print("\n🎉 CONFIGURACIÓN COMPLETADA")
    print("=" * 60)
    print("✅ Ahora los usuarios recibirán correos de bienvenida al registrarse con Google")
    print("✅ Reinicia la aplicación para aplicar los cambios: python app.py")
    print("✅ Prueba el login con Google para verificar el envío de correos")

if __name__ == "__main__":
    main()