@echo off
setlocal enabledelayedexpansion
echo ========================================
echo SIF - Custom Tunnel Setup
echo ========================================
echo.

REM Check if logged in
cloudflared tunnel list >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [1/4] Login to Cloudflare...
    echo.
    echo A browser will open. Select your account and authorize.
    echo.
    pause
    cloudflared tunnel login
    echo.
) else (
    echo [1/4] Already logged in to Cloudflare.
)

echo.
echo [2/4] Enter your tunnel name (or press Enter for 'sif'):
set /p TUNNEL_NAME="Tunnel name: "
if "!TUNNEL_NAME!"=="" set TUNNEL_NAME=sif

echo.
echo Checking if tunnel exists...
cloudflared tunnel info !TUNNEL_NAME! >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Tunnel '!TUNNEL_NAME!' already exists.
    set /p CONTINUE="Create a new tunnel with different name? (y/n): "
    if /i "!CONTINUE!"=="y" (
        set /p TUNNEL_NAME="Enter new tunnel name: "
        cloudflared tunnel create !TUNNEL_NAME!
    )
) else (
    echo Creating tunnel '!TUNNEL_NAME!'...
    cloudflared tunnel create !TUNNEL_NAME!
)

echo.
echo [3/4] Getting tunnel ID...
for /f "tokens=2" %%i in ('cloudflared tunnel info !TUNNEL_NAME! ^| findstr /i "id"') do set TUNNEL_ID=%%i
echo Tunnel ID: !TUNNEL_ID!

echo.
echo [4/4] Configure your domain.
set /p SUBDOMAIN="Enter subdomain (e.g. api): "
set /p DOMAIN="Enter your domain (e.g. example.com): "

echo.
echo Creating DNS record: %SUBDOMAIN%.%DOMAIN% -^> !TUNNEL_NAME!
cloudflared tunnel route dns !TUNNEL_NAME! %SUBDOMAIN%.%DOMAIN%

echo.
echo Creating config.yml...
(
echo tunnel: !TUNNEL_ID!
echo credentials-file: %%USERPROFILE%%\.cloudflared\!TUNNEL_ID!.json
echo.
echo ingress:
echo   - hostname: %SUBDOMAIN%.%DOMAIN%
echo     service: http://localhost:5000
echo   - service: http_status:404
) > config.yml

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Your tunnel URL: https://%SUBDOMAIN%.%DOMAIN%
echo.
echo Config saved to: config.yml
echo.
echo To start the tunnel:
echo   1. Run: python main.py
echo   2. In new terminal: tunnel-start.bat
echo.
echo NOTE: Edit config.yml and update tunnel name in tunnel-start.bat
echo       if you used a custom name.
echo.
pause
