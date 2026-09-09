@echo off
echo ===================================
echo  FYP - Dynamic E-Shopping Platform
echo ===================================
echo.

cd /d "%~dp0backend\fyp-backend"

if exist "venv_new\Scripts\python.exe" (
    echo Starting server...
    echo.
    echo  Open this URL in your browser:
    echo  http://127.0.0.1:5000
    echo.
    echo  Press Ctrl+C to stop the server.
    echo ===================================
    venv_new\Scripts\python app.py
) else if exist "venv\Scripts\python.exe" (
    echo Starting server with venv...
    echo.
    echo  Open this URL in your browser:
    echo  http://127.0.0.1:5000
    echo.
    venv\Scripts\python app.py
) else (
    echo ERROR: No virtual environment found.
    echo Run this first in backend\fyp-backend folder:
    echo   python -m venv venv_new
    echo   venv_new\Scripts\pip install -r requirements.txt
    pause
)
