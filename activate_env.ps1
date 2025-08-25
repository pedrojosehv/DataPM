# Script para activar el entorno virtual DataPM
Write-Host "Activando entorno virtual DataPM..." -ForegroundColor Green
& "local_data\tools\env\Scripts\Activate.ps1"
Write-Host "Entorno virtual activado. Python: $env:VIRTUAL_ENV\Scripts\python.exe" -ForegroundColor Green
