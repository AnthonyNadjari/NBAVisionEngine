@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat 2>nul
if not exist .venv\Scripts\activate.bat (
    echo Run setup.bat first.
    pause
    exit /b 1
)
if not exist .env (
    echo Creating .env with secret...
    python -c "import secrets; open('.env','w').write('NBAVISION_SECRET='+secrets.token_urlsafe(32)+chr(10))"
    echo Secret saved to .env. Use it for X-API-KEY when triggering.
)
echo Starting server on http://127.0.0.1:8000
echo In another terminal run: cloudflared tunnel --url http://localhost:8000
echo.
uvicorn server:app --host 127.0.0.1 --port 8000
pause
