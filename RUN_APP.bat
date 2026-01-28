@echo off
cd /d "%~dp0"
title Flexo Inspection Launcher
echo ===================================================
echo   Starting Flexo Inspection System
echo ===================================================
echo.

:: 0. Activate Virtual Environment
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found in .venv!
    echo Please make sure you have created the python environment.
    pause
    exit
)
echo [0/3] Activating Python Environment...
call .venv\Scripts\activate.bat

:: 1. Start Backend on Port 8001
echo [1/3] Starting Backend Server (Port 8001)...
:: We use a separate cmd window for the backend, activating venv inside it too
start "Flexo Backend" cmd /k "call .venv\Scripts\activate.bat && cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8001"

:: 2. Start Frontend
echo [2/3] Starting Frontend Client...
start "Flexo Frontend" cmd /k "cd frontend && npm run dev"

:: 3. Open Browser
echo [3/3] Launching Browser in 5 seconds...
timeout /t 5 >nul
start http://localhost:5173

echo.
echo System Started! 
echo.
echo If you see "Connection Failed" in the browser:
echo 1. Check the "Flexo Backend" terminal window for errors.
echo 2. Ensure no other instances are running.
echo.
pause
