@echo off
echo ============================================
echo   Bengali OCR - Tauri Dev Mode
echo ============================================
echo.
echo Setting up environment...
echo.

rem --- MinGW Path Setup ---
if exist C:\mingw64\mingw64\bin\dlltool.exe (
    set PATH=C:\mingw64\mingw64\bin;%PATH%
    echo [OK] MinGW found at C:\mingw64
) else if exist C:\mingw64\bin\dlltool.exe (
    set PATH=C:\mingw64\bin;%PATH%
    echo [OK] MinGW found at C:\mingw64
) else (
    echo [WARN] MinGW not found at C:\mingw64
    echo Rust compilation may fail. Set PATH to MinGW bin directory.
)

rem --- CARGO_TARGET_DIR to avoid spaces in path issues ---
if not exist C:\build-cache mkdir C:\build-cache
set CARGO_TARGET_DIR=C:\build-cache
echo [OK] Build cache: C:\build-cache

rem --- Check Python ---
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found in PATH
    pause
    exit /b 1
) else (
    echo [OK] Python found
)

rem --- Check Node.js ---
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js not found in PATH
    pause
    exit /b 1
) else (
    echo [OK] Node.js found
)

rem --- Check Rust ---
rustc --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Rust not found in PATH
    pause
    exit /b 1
) else (
    echo [OK] Rust found
)

echo.
echo ============================================
echo   Starting Tauri Development Mode
echo ============================================
echo.
echo The app will open in a native desktop window.
echo Close the window to stop all processes.
echo.

cd /d "%~dp0"

if not exist src-tauri (
    echo [ERROR] Run this script from the project root
    pause
    exit /b 1
)

rem --- IMPORTANT: Run tauri from project root (where src-tauri/ lives) ---
echo [INFO] Starting Tauri (this will also start the frontend dev server)...
echo.
npx tauri dev

echo.
echo App closed.
pause
