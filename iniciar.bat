@echo off
setlocal
cd /d "%~dp0"

echo [1/4] Verificando entorno virtual...
if not exist "venv\Scripts\activate.bat" (
    echo Creando entorno virtual venv...
    python -m venv venv 2>nul || py -m venv venv
)

echo [2/4] Activando entorno virtual...
call venv\Scripts\activate.bat

echo [3/4] Instalando dependencias...
pip install -r requirements.txt

echo [4/4] Aplicando migraciones...
python manage.py migrate --noinput

echo.
echo ======================================================
echo   Servidor iniciado en http://127.0.0.1:8000/
echo   Presione CTRL+C para detener el servidor.
echo ======================================================
echo.
python manage.py runserver
