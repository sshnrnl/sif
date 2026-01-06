@echo off
echo ========================================
echo SIF - Cloudflare Tunnel
echo ========================================
echo.

REM Check if cloudflared is installed
where cloudflared >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo cloudflared not found!
    echo.
    echo Installing cloudflared...
    winget install --id Cloudflare.cloudflared --accept-package-agreements --accept-source-agreements
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo Installation failed. Please install manually:
        echo   https://github.com/cloudflare/cloudflared/releases
        echo.
        pause
        exit /b 1
    )
    echo.
    echo Installation complete! Please run this script again.
    pause
    exit /b 0
)

echo Starting tunnel to http://localhost:5000
echo.
echo Press Ctrl+C to stop the tunnel
echo.

cloudflared tunnel --url http://localhost:5000
