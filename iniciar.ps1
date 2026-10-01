Set-Location $PSScriptRoot

Write-Host "[1/4] Verificando entorno virtual..."
if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "Creando entorno virtual venv..."
    python -m venv venv
}

Write-Host "[2/4] Activando entorno virtual..."
$env:VIRTUAL_ENV = "$PSScriptRoot\venv"
$env:PATH = "$PSScriptRoot\venv\Scripts;$env:PATH"

Write-Host "[3/4] Instalando dependencias..."
pip install -r requirements.txt

Write-Host "[4/4] Aplicando migraciones..."
python manage.py migrate --noinput

Write-Host ""
Write-Host "======================================================"
Write-Host "  Servidor iniciado en http://127.0.0.1:8000/"
Write-Host "  Presione CTRL+C para detener el servidor."
Write-Host "======================================================"
Write-Host ""
python manage.py runserver
