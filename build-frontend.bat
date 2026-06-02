@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   PT-ONNX Benchmark Tool v2.0
echo   Build Frontend for Production
echo ========================================
echo.

set "ROOT_DIR=%~dp0"

:: Check Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found!
    echo Please install Node.js 16+ from: https://nodejs.org/
    pause
    exit /b 1
)

:: Check if frontend directory exists
if not exist "%ROOT_DIR%frontend\package.json" (
    echo [ERROR] frontend\package.json not found!
    pause
    exit /b 1
)

:: Install dependencies
echo [1/2] Installing frontend dependencies...
cd /d "%ROOT_DIR%frontend"
call npm install
if %errorlevel% neq 0 (
    echo [ERROR] npm install failed
    pause
    exit /b 1
)

:: Build
echo.
echo [2/2] Building frontend...
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

:: Done
echo.
echo ========================================
echo   Build Complete!
echo ========================================
echo.
echo Frontend output: frontend\dist\
echo.
echo You can now run start.bat to start the application.
echo.
pause
