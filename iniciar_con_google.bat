@echo off
echo ========================================
echo        EnerVirgil con Google OAuth
echo ========================================
echo.

echo 📋 Cargando configuracion...

REM Cargar variables del archivo .env
for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
    if not "%%a"=="" if not "%%a"=="REM" if not "%%a"=="#" (
        set "%%a=%%b"
        echo   ✅ %%a configurado
    )
)

echo.
echo 🚀 Iniciando EnerVirgil...
echo 🌐 La aplicacion estara disponible en: http://localhost:5000
echo 📱 Ahora puedes usar "Iniciar sesion con Google"
echo.

python app.py

echo.
echo 👋 Aplicacion cerrada
pause