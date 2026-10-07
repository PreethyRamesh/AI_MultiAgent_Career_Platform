@echo off
setlocal
title AI MultiAgent Career Platform
echo ============================================
echo   AI MultiAgent Career Platform - Launcher
echo ============================================

REM --- folder where this script lives ---
set "APP=%~dp0"
cd /d "%APP%"

REM --- venv python interpreter ---
set "PY=%APP%.venv\Scripts\python.exe"
if not exist "%PY%" (
    echo [ERROR] Virtual environment not found: %PY%
    echo Create it first with:  python -m venv .venv
    echo Then install deps:     .venv\Scripts\pip install -r backend\requirements.txt -r person3-dashboard\requirements.txt
    pause
    exit /b 1
)

echo.
echo [1/2] Starting AI Learning and Career API  -^> http://127.0.0.1:8000
pushd "%APP%backend"
start "AI Learning + Career API (:8000)" cmd /k ""%PY%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
popd

echo [2/2] Starting Progress Dashboard          -^> http://127.0.0.1:8001
set DEMO_MODE=false
set STATE_API_BASE_URL=http://127.0.0.1:8000
pushd "%APP%person3-dashboard"
start "Progress Dashboard (:8001)" cmd /k ""%PY%" -m uvicorn main:app --host 127.0.0.1 --port 8001"
popd

echo.
echo Opening the app in your browser...
timeout /t 5 /nobreak >nul
start "" http://127.0.0.1:8000/

echo.
echo Done! Running windows:
echo    :8000  AI Learning and Guidance (Person 2) / Career Analysis (Person 1)
echo    :8001  ProgressLab Dashboard (Person 3)
echo Close the two server windows to stop the app.
pause