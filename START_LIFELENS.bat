@echo off

title LifeLens AI

cd /d "%~dp0"

echo.
echo ==========================================
echo              LIFELENS AI
echo        ONE-CLICK PROJECT LAUNCHER
echo ==========================================
echo.

echo Starting LifeLens Activity Tracker...
echo.

start "LifeLens Tracker" /min cmd /k python tracker.py

timeout /t 3 /nobreak >nul

echo.
echo Starting LifeLens AI Dashboard...
echo.

streamlit run app.py

pause