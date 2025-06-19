#!/usr/bin/env python3
"""
Script para solucionar el error redirect_uri_mismatch
"""

import webbrowser
import time

def mostrar_problema():
    print("🚨 ERROR DETECTADO: redirect_uri_mismatch")
    print("=" * 50)
    print("Este error significa que la URI de redirección en Google Cloud Console")
    print("no coincide con la que está usando la aplicación.")
    print()
    print("🔍 URI que está usando la aplicación:")
    print("   http://localhost:5000/auth/google/callback")
    print()
    print("❌ Posibles causas:")
    print("   1. URI mal configurada en Google Cloud Console")
    print("   2. Diferencia entre localhost y 127.0.0.1")
    print("   3. Puerto incorrecto")
    print("   4. Protocolo incorrecto (http vs https)")

def abrir_google_console():
    print("\n🌐 Abriendo Google Cloud Console...")
    webbrowser.open("https://console.cloud.google.com/apis/credentials")
    time.sleep(2)

def mostrar_solucion():
    print("\n" + "=" * 60)
    print("🔧 SOLUCIÓN PASO A PASO")
    print("=" * 60)
    
    print("\n📋 PASO 1: Abrir Google Cloud Console")
    abrir_google_console()
    
    print("\n📝 PASO 2: Editar las credenciales OAuth")
    print("1. ✅ Busca tu credencial 'EnerVirgil OAuth Client'")
    print("2. ✅ Haz clic en el ícono de editar (lápiz)")
    print("3. ✅ Ve a la sección 'URIs de redirección autorizados'")
    
    print("\n🔄 PASO 3: Configurar URIs correctas")
    print("ELIMINA todas las URIs existentes y agrega EXACTAMENTE estas:")
    print()
    print("📋 URI 1: http://localhost:5000/auth/google/callback")
    print("📋 URI 2: http://127.0.0.1:5000/auth/google/callback")
    print()
    print("⚠️ IMPORTANTE:")
    print("   - Usa exactamente 'localhost' y '127.0.0.1'")
    print("   - Usa exactamente el puerto '5000'")
    print("   - Usa 'http://' (no https)")
    print("   - No agregues barras finales '/'")
    
    print("\n💾 PASO 4: Guardar cambios")
    print("1. ✅ Haz clic en 'GUARDAR'")
    print("2. ✅ Espera a que se guarden los cambios")
    print("3. ✅ Cierra el navegador")
    
    input("\n⏳ Presiona ENTER cuando hayas completado la configuración...")

def verificar_configuracion():
    print("\n" + "=" * 60)
    print("🔍 VERIFICACIÓN DE LA CONFIGURACIÓN")
    print("=" * 60)
    
    print("\n📋 Verifica que tengas EXACTAMENTE estas URIs:")
    print("✅ URIs de origen autorizados:")
    print("   - http://localhost:5000")
    print("   - http://127.0.0.1:5000")
    print()
    print("✅ URIs de redirección autorizados:")
    print("   - http://localhost:5000/auth/google/callback")
    print("   - http://127.0.0.1:5000/auth/google/callback")
    
    print("\n❌ NO debe haber:")
    print("   - https:// (solo http://)")
    print("   - Puertos diferentes a 5000")
    print("   - Barras finales /")
    print("   - Espacios en blanco")

def mostrar_solucion_alternativa():
    print("\n" + "=" * 60)
    print("🔄 SOLUCIÓN ALTERNATIVA")
    print("=" * 60)
    
    print("\nSi el problema persiste, también puedes:")
    print("1. 🗑️ Eliminar la credencial actual")
    print("2. 🆕 Crear una nueva credencial OAuth")
    print("3. 🔧 Configurar las URIs desde cero")
    print("4. 📋 Actualizar el archivo .env con las nuevas credenciales")

def main():
    print("🔧 SOLUCIONADOR DE redirect_uri_mismatch")
    print("=" * 50)
    
    mostrar_problema()
    
    print("\n🚀 ¿Quieres que te ayude a solucionarlo?")
    respuesta = input("Escribe 'si' para continuar: ").lower().strip()
    
    if respuesta in ['si', 'sí', 's', 'yes', 'y']:
        mostrar_solucion()
        verificar_configuracion()
        
        print("\n" + "=" * 60)
        print("✅ CONFIGURACIÓN COMPLETADA")
        print("=" * 60)
        
        print("\n🚀 Próximos pasos:")
        print("1. ✅ Cierra la aplicación actual (Ctrl+C)")
        print("2. ✅ Ejecuta: python app.py")
        print("3. ✅ Ve a: http://localhost:5000")
        print("4. ✅ Prueba 'Iniciar sesión con Google'")
        
        print("\n💡 Si el problema persiste:")
        print("- Espera 5-10 minutos (Google puede tardar en actualizar)")
        print("- Verifica que las URIs sean exactamente como se muestran")
        print("- Usa modo incógnito en el navegador")
        
        mostrar_solucion_alternativa()
        
    else:
        print("\n📋 Resumen rápido de la solución:")
        print("1. Ve a: https://console.cloud.google.com/apis/credentials")
        print("2. Edita tu credencial OAuth")
        print("3. Configura URI de redirección: http://localhost:5000/auth/google/callback")
        print("4. Guarda los cambios")
        print("5. Reinicia la aplicación")

if __name__ == "__main__":
    main()
    input("\nPresiona ENTER para salir...")