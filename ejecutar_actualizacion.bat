@echo off
cd /d "%~dp0"
python actualizar_google_ads.py
python actualizar_dashboard.py

echo.
echo Subiendo cambios a GitHub...
git add Dashboard_ALMI.html ads_data.json
git commit -m "Actualizacion automatica del dashboard"
git push

echo.
echo Presiona una tecla para cerrar...
pause >nul
