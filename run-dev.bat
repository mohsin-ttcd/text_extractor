@echo off
title Bengali OCR - Dev Mode
echo ============================================
echo   Bengali OCR - Backend + Frontend
echo ============================================
echo.

rem --- Check Python ---
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found. Install from https://python.org
    pause
    exit /b 1
)
echo [OK] Python found

rem --- Check Node.js ---
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js not found. Install from https://nodejs.org
    pause
    exit /b 1
)
echo [OK] Node.js found

rem --- Kill any process already using port 8000 or 5173 ---
echo.
echo [INFO] Clearing ports 8000 and 5173 if busy...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 :5173" 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 1 /nobreak >nul
echo [OK] Ports cleared

rem --- Install frontend deps if missing ---
if not exist "frontend\node_modules" (
    echo [INFO] Installing frontend dependencies (first time only)...
    cd frontend
    npm install
    cd ..
)

echo.
echo ============================================
echo Starting servers...
echo ============================================

rem --- Start Backend in new window ---
start "Bengali OCR Backend :8000" cmd /k "color 0A && title BACKEND :8000 && echo Starting FastAPI backend... && python backend/run.py"

echo [OK] Backend window opened - waiting to boot...
timeout /t 3 /nobreak >nul

rem --- Start Frontend in new window ---
start "Bengali OCR Frontend :5173" cmd /k "color 0B && title FRONTEND :5173 && echo Starting Vite frontend... && cd frontend && npm run dev"

echo [OK] Frontend window opened - waiting to compile...
timeout /t 5 /nobreak >nul

echo.
echo ============================================
echo   App is ready!
echo.
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173  ^<-- open this
echo   API Docs: http://localhost:8000/docs
echo.
echo   To STOP: close the two colored windows
echo ============================================
echo.

rem --- Open browser ---
start http://localhost:5173

pause
