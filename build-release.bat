@echo off
echo ============================================
echo   Bengali OCR - Production Build
echo ============================================
echo.
echo This builds the complete Windows desktop installer.
echo.

cd /d "%~dp0"

rem --- Environment Setup ---
if exist C:\mingw64\mingw64\bin\dlltool.exe (
    set PATH=C:\mingw64\mingw64\bin;%PATH%
)
if not exist C:\build-cache mkdir C:\build-cache
set CARGO_TARGET_DIR=C:\build-cache

echo [1/4] Building Python backend executable...
if exist dist\backend.exe (
    echo Backend executable already exists. Skipping...
) else (
    pyinstaller backend.spec --clean --noconfirm
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Backend build failed!
        pause
        exit /b 1
    )
    echo [OK] Backend built: dist\backend.exe
)

echo [2/4] Installing frontend dependencies...
cd frontend
call npm install
cd ..

echo [3/4] Building Tauri application...
cd frontend
call npx tauri build
cd ..

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Tauri build failed!
    pause
    exit /b 1
)

echo.
echo ============================================
echo   BUILD COMPLETE!
echo ============================================
echo.
echo Installer location:
echo   src-tauri\target\release\bundle\nsis\Bengali OCR Setup*.exe
echo.
echo Minimum system requirements:
echo   - Windows 10 or later
echo   - WebView2 Runtime (pre-installed on Win10+)
echo   - 4GB RAM recommended
echo.
pause
