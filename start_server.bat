@echo off
REM NBAVision webhook server — Windows
REM Set NBAVISION_SECRET before running. Edit paths as needed.

cd /d "%~dp0"
if not defined NBAVISION_SECRET (
    echo Set NBAVISION_SECRET first: set NBAVISION_SECRET=your_secret
    exit /b 1
)
if exist .venv\Scripts\uvicorn.exe (
    .venv\Scripts\uvicorn server:app --host 127.0.0.1 --port 8000
) else (
    python -m uvicorn server:app --host 127.0.0.1 --port 8000
)
