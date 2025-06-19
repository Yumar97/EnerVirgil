# 🚀 Guía Completa de Despliegue - EnerVirgil

## 📋 Preparación Completada

He preparado todos los archivos necesarios para subir EnerVirgil a la web. Aquí tienes la guía paso a paso:

## 🔧 Archivos Creados para el Despliegue

### ✅ **Archivos de Configuración**
- `requirements.txt` - Dependencias actualizadas con Gunicorn
- `Procfile` - Comando de inicio para el servidor
- `gunicorn.conf.py` - Configuración del servidor web
- `runtime.txt` - Versión de Python especificada
- `render.yaml` - Configuración específica para Render
- `.gitignore` - Archivos a excluir del repositorio
- `.env.production` - Template de variables de entorno

### ✅ **Modificaciones en el Código**
- URLs dinámicas en templates de correo
- Configuración de producción vs desarrollo
- Soporte para HTTPS en producción
- Variables de entorno para URLs base

## 🌐 Opción 1: Despliegue en Render (Recomendado)

### **Paso 1: Crear Cuenta en Render**
1. Ve a [render.com](https://render.com)
2. Regístrate con tu cuenta de GitHub
3. Conecta tu repositorio de GitHub

### **Paso 2: Subir Código a GitHub**
```bash
# En tu terminal, navega a la carpeta del proyecto
cd "C:\Users\yumar\OneDrive\Escritorio\EnerVirgil"

# Inicializar repositorio Git
git init

# Agregar archivos
git add .

# Hacer commit inicial
git commit -m "Initial commit - EnerVirgil ready for deployment"

# Conectar con GitHub (reemplaza con tu repositorio)
git remote add origin https://github.com/tu-usuario/enervirgil.git

# Subir código
git push -u origin main
```

### **Paso 3: Crear Web Service en Render**
1. En Render Dashboard, click "New +"
2. Selecciona "Web Service"
3. Conecta tu repositorio de GitHub
4. Configuración:
   - **Name**: `enervirgil`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --config gunicorn.conf.py app:app`

### **Paso 4: Configurar Variables de Entorno**
En Render, ve a Environment y agrega:

```
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_SECRET_KEY=tu_clave_secreta_super_segura_aqui_cambiar
BASE_URL=https://tu-app.onrender.com

# Configuración de correo Gmail
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=tu_email@gmail.com
MAIL_PASSWORD=tu_app_password_de_gmail
MAIL_DEFAULT_SENDER=tu_email@gmail.com

# Google OAuth (obtener de Google Cloud Console)
GOOGLE_CLIENT_ID=tu_google_client_id
GOOGLE_CLIENT_SECRET=tu_google_client_secret
```

### **Paso 5: Configurar Google OAuth**
1. Ve a [Google Cloud Console](https://console.cloud.google.com)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la API de Google OAuth
4. Crea credenciales OAuth 2.0
5. Agrega tu dominio de Render a "Authorized redirect URIs":
   - `https://tu-app.onrender.com/auth/google/callback`

## 🌐 Opción 2: Despliegue en Railway

### **Paso 1: Crear Cuenta en Railway**
1. Ve a [railway.app](https://railway.app)
2. Regístrate con GitHub
3. Click "New Project" → "Deploy from GitHub repo"

### **Paso 2: Configurar Variables de Entorno**
Mismas variables que en Render, pero en Railway Dashboard.

## 🌐 Opción 3: Despliegue en Heroku

### **Paso 1: Instalar Heroku CLI**
1. Descarga [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. Instala y reinicia terminal

### **Paso 2: Desplegar**
```bash
# Login en Heroku
heroku login

# Crear app
heroku create tu-app-enervirgil

# Configurar variables de entorno
heroku config:set FLASK_ENV=production
heroku config:set FLASK_SECRET_KEY=tu_clave_secreta
heroku config:set BASE_URL=https://tu-app-enervirgil.herokuapp.com
# ... agregar todas las demás variables

# Desplegar
git push heroku main
```

## 📧 Configuración de Gmail para Correos

### **Paso 1: Habilitar App Passwords**
1. Ve a tu cuenta de Google
2. Seguridad → Verificación en 2 pasos (debe estar habilitada)
3. Contraseñas de aplicaciones
4. Genera una nueva contraseña para "EnerVirgil"
5. Usa esta contraseña en `MAIL_PASSWORD`

### **Paso 2: Configurar Variables de Correo**
```
MAIL_USERNAME=tu_email@gmail.com
MAIL_PASSWORD=la_app_password_generada
MAIL_DEFAULT_SENDER=tu_email@gmail.com
```

## 🔐 Configuración de Google OAuth

### **Paso 1: Google Cloud Console**
1. Ve a [console.cloud.google.com](https://console.cloud.google.com)
2. Crea proyecto "EnerVirgil"
3. APIs y servicios → Biblioteca
4. Busca y habilita "Google+ API"

### **Paso 2: Crear Credenciales**
1. APIs y servicios → Credenciales
2. Crear credenciales → ID de cliente OAuth 2.0
3. Tipo: Aplicación web
4. URIs de redirección autorizados:
   - `https://tu-dominio.onrender.com/auth/google/callback`
   - `http://localhost:5000/auth/google/callback` (para desarrollo)

### **Paso 3: Configurar Variables**
```
GOOGLE_CLIENT_ID=tu_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu_client_secret
```

## 🗄️ Base de Datos

EnerVirgil usa SQLite que funciona perfectamente en Render. La base de datos se crea automáticamente en el primer inicio.

## 🔍 Verificación del Despliegue

### **Checklist Post-Despliegue**
- [ ] La aplicaci��n carga correctamente
- [ ] El login funciona
- [ ] Google OAuth funciona
- [ ] Los correos se envían correctamente
- [ ] Las rutas de prueba funcionan:
  - `/preview_email/nuevo`
  - `/preview_email/vuelta`
  - `/test_email`

### **URLs de Prueba**
Una vez desplegado, prueba:
- `https://tu-app.onrender.com` - Página principal
- `https://tu-app.onrender.com/login` - Login
- `https://tu-app.onrender.com/preview_email/nuevo` - Preview correo nuevo
- `https://tu-app.onrender.com/test_email` - Prueba de correos

## 🚨 Solución de Problemas Comunes

### **Error: Application failed to start**
- Verifica que todas las variables de entorno estén configuradas
- Revisa los logs en Render Dashboard

### **Error: Google OAuth no funciona**
- Verifica que las URLs de redirección estén correctas
- Asegúrate de que el dominio esté autorizado en Google Cloud

### **Error: No se envían correos**
- Verifica la configuración de Gmail App Password
- Revisa que `MAIL_USERNAME` y `MAIL_PASSWORD` sean correctos

### **Error: Base de datos**
- SQLite se crea automáticamente, no requiere configuración adicional

## 📊 Monitoreo y Logs

### **En Render:**
- Ve a tu servicio → Logs para ver errores
- Metrics para ver rendimiento

### **Comandos útiles:**
```bash
# Ver logs en tiempo real (si usas Heroku)
heroku logs --tail

# Reiniciar aplicación
heroku restart
```

## 🔄 Actualizaciones Futuras

Para actualizar la aplicación:
```bash
# Hacer cambios en el código
git add .
git commit -m "Descripción de cambios"
git push origin main
```

Render se actualizará automáticamente cuando hagas push a GitHub.

## 🎯 Próximos Pasos Recomendados

1. **Dominio Personalizado**: Configura un dominio propio
2. **SSL/HTTPS**: Render lo incluye gratis
3. **Monitoreo**: Configura alertas de uptime
4. **Backup**: Programa backups de la base de datos
5. **CDN**: Para servir archivos estáticos más rápido

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs de la aplicación
2. Verifica las variables de entorno
3. Consulta la documentación de Render
4. Revisa que todas las URLs estén actualizadas

---

**¡EnerVirgil está listo para el mundo! 🌍⚡**

*Tu asistente inteligente para el ahorro energético, ahora disponible 24/7 en la web.*