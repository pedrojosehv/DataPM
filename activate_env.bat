@echo off
echo Activando entorno virtual DataPM...
call "local_data\tools\env\Scripts\activate.bat"
echo Entorno virtual activado. Python: %VIRTUAL_ENV%\Scripts\python.exe
cmd /k
