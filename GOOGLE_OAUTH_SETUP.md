# Configuración de Google OAuth para EnerVirgil

## Pasos para configurar Google OAuth

### 1. Crear un proyecto en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la API de Google+ (Google People API)

### 2. Configurar OAuth 2.0

1. Ve a "APIs y servicios" > "Credenciales"
2. Haz clic en "Crear credenciales" > "ID de cliente de OAuth 2.0"
3. Selecciona "Aplicación web"
4. Configura las URIs autorizadas:
   - **URIs de origen autorizados**: `http://localhost:5000`
   - **URIs de redirección autorizados**: `http://localhost:5000/auth/google/callback`

### 3. Obtener las credenciales

1. Copia el **Client ID** y **Client Secret**
2. Crea un archivo `.env` en la raíz del proyecto (copia de `.env.example`)
3. Reemplaza los valores:
   ```
   GOOGLE_CLIENT_ID=tu_client_id_real_aqui
   GOOGLE_CLIENT_SECRET=tu_client_secret_real_aqui
   ```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5. Configurar variables de entorno

#### Opción A: Archivo .env (recomendado para desarrollo)
```bash
# Copia el archivo de ejemplo
cp .env.example .env
# Edita .env con tus credenciales reales
```

#### Opción B: Variables de entorno del sistema
```bash
export GOOGLE_CLIENT_ID="tu_client_id_aqui"
export GOOGLE_CLIENT_SECRET="tu_client_secret_aqui"
export FLASK_SECRET_KEY="una_clave_secreta_muy_segura"
```

### 6. Ejecutar la aplicación

```bash
python app.py
```

## Configuración para producción

### Para producción, actualiza las URIs en Google Cloud Console:

- **URIs de origen autorizados**: `https://tu-dominio.com`
- **URIs de redirección autorizados**: `https://tu-dominio.com/auth/google/callback`

### Variables de entorno en producción:
```bash
FLASK_ENV=production
FLASK_DEBUG=False
GOOGLE_CLIENT_ID=tu_client_id_de_produccion
GOOGLE_CLIENT_SECRET=tu_client_secret_de_produccion
FLASK_SECRET_KEY=clave_secreta_muy_segura_para_produccion
```

## Funcionalidades implementadas

✅ **Inicio de sesión con Google**
- Los usuarios pueden iniciar sesión con su cuenta de Gmail
- Se crea automáticamente una cuenta en el sistema
- Se sincroniza información básica (nombre, email, foto de perfil)

✅ **Gestión de usuarios híbrida**
- Usuarios locales (registro tradicional)
- Usuarios de Google OAuth
- Prevención de conflictos entre cuentas

✅ **Completar perfil**
- Los usuarios de Google pueden agregar información adicional
- DNI, teléfono, número de recibo (opcionales)
- Acceso a funciones completas del sistema

✅ **Seguridad**
- Separación entre métodos de autenticación
- Validación de datos
- Protección contra cuentas duplicadas

## Solución de problemas

### Error: "redirect_uri_mismatch"
- Verifica que las URIs en Google Cloud Console coincidan exactamente
- Asegúrate de incluir el protocolo (http:// o https://)
- No incluyas barras finales en las URIs

### Error: "invalid_client"
- Verifica que GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET sean correctos
- Asegúrate de que las variables de entorno estén cargadas

### Error: "access_denied"
- El usuario canceló la autorización
- Verifica que el proyecto de Google Cloud esté configurado correctamente

## Notas importantes

- En desarrollo, usa `http://localhost:5000`
- En producción, usa HTTPS obligatoriamente
- Mantén las credenciales seguras y nunca las subas a repositorios públicos
- El archivo `.env` está en `.gitignore` por seguridad