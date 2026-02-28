@echo off
REM One-time setup: create venv, install deps, Playwright
cd /d "%~dp0"

if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate.bat

echo Installing Python packages...
pip install -r requirements.txt
echo Installing Playwright Chromium...
playwright install chromium

echo.
echo Setup done. Next: run login_once.bat to log into X, then run_server.bat
