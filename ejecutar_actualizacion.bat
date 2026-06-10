@echo off
cd /d "%~dp0"
python actualizar_google_ads.py
python actualizar_dashboard.py
echo.
echo Presiona una tecla para cerrar...
pause >nul
