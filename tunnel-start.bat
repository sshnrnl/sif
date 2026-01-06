@echo off
echo ========================================
echo SIF - Custom Domain Tunnel
echo ========================================
echo.

if not exist config.yml (
    echo ERROR: config.yml not found!
    echo.
    echo First, run: tunnel-setup.bat
    echo.
    pause
    exit /b 1
)

echo Reading tunnel configuration...
for /f "tokens=2" %%i in ('findstr /i "tunnel:" config.yml') do set TUNNEL_ID=%%i
set TUNNEL_ID=%TUNNEL_ID: =%

echo Tunnel ID: %TUNNEL_ID%
echo.
echo Starting tunnel...
echo Press Ctrl+C to stop
echo.

cloudflared tunnel --config config.yml run %TUNNEL_ID%
