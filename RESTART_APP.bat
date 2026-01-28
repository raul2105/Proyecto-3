@echo off
cd /d "%~dp0"
echo ===================================================
echo   Restarting Flexo Inspection System
echo ===================================================
echo.

:: Close existing backend and frontend windows
echo [1/3] Closing Backend/Frontend windows...
taskkill /FI "WINDOWTITLE eq Flexo Backend" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Flexo Frontend" /T /F >nul 2>&1

:: Small wait to ensure ports are released
echo [2/3] Waiting for processes to stop...
timeout /t 2 >nul

:: Start everything again
echo [3/3] Starting system...
call "%~dp0RUN_APP.bat"

echo.
echo Logs are stored in: %~dp0backend\logs
