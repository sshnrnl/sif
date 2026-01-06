@echo off
echo ========================================
echo SIF - Setup Script
echo ========================================
echo.

REM Check if .env exists, if not copy from example
if not exist .env (
    echo [1/4] Creating .env from .env.example...
    copy .env.example .env >nul
    echo     EDIT .env with your database credentials!
) else (
    echo [1/4] .env already exists, skipping...
)

echo.
echo [2/4] Creating virtual environment...
python -m venv venv

echo.
echo [3/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [4/4] Installing dependencies...
pip install -r requirements.txt

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To run the server:
echo   python main.py
echo.
echo To start tunnel (after server is running):
echo   tunnel.bat
echo.
pause
