@echo off
echo ========================================
echo SIF - Start Server + Tunnel
echo ========================================
echo.

echo [1/2] Starting Flask server on port 5000...
echo.

start /B python main.py

timeout /t 3 /nobreak >nul

echo.
echo [2/2] Starting Cloudflare tunnel...
echo.
echo URL: https://scrapper.cosplay.co.id
echo Press Ctrl+C to stop
echo.

cloudflared tunnel --config config.yml run 865a1e37-e9d3-406c-8557-921bc39e5a0b

pause
