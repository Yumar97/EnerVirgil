@echo off
echo ========================================
echo   Configuracion de Google OAuth
echo ========================================
echo.

echo Para obtener las credenciales:
echo 1. Ve a: https://console.cloud.google.com/
echo 2. Crea un proyecto y habilita Google+ API
echo 3. Ve a "Credenciales" y crea "ID de cliente OAuth 2.0"
echo 4. Configura:
echo    - Origen autorizado: http://localhost:5000
echo    - URI de redireccion: http://localhost:5000/auth/google/callback
echo.

set /p CLIENT_ID="Ingresa tu Google Client ID: "
set /p CLIENT_SECRET="Ingresa tu Google Client Secret: "

if "%CLIENT_ID%"=="" (
    echo Error: Client ID es requerido
    pause
    exit /b 1
)

if "%CLIENT_SECRET%"=="" (
    echo Error: Client Secret es requerido
    pause
    exit /b 1
)

echo.
echo Configurando variables de entorno...
set GOOGLE_CLIENT_ID=%CLIENT_ID%
set GOOGLE_CLIENT_SECRET=%CLIENT_SECRET%
set FLASK_SECRET_KEY=clave_secreta_super_segura_para_desarrollo

echo.
echo ✅ Variables configuradas exitosamente!
echo.
echo Iniciando aplicacion...
python app.py

pause