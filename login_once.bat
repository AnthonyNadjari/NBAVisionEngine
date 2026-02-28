@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat 2>nul
if not exist .venv\Scripts\activate.bat (
    echo Run setup.bat first.
    pause
    exit /b 1
)
echo Opening browser. Log into X, then press Enter here.
python login_once.py
pause
