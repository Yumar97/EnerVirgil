@echo off
echo Cargando variables de entorno...
for /f "delims=" %%x in (.env) do (
    set "%%x"
)
echo Variables cargadas. Iniciando aplicacion...
python app.py
pause