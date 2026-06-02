@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   PT-ONNX Benchmark Tool v2.0
echo ========================================
echo.

:: Get script directory
set "ROOT_DIR=%~dp0"
set "BACKEND_DIR=%ROOT_DIR%backend"

:: Check virtualenv
if not exist "%BACKEND_DIR%\.venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run setup.bat first.
    pause
    exit /b 1
)

:: Activate virtualenv
call "%BACKEND_DIR%\.venv\Scripts\activate.bat"

:: Check if main.py exists
if not exist "%BACKEND_DIR%\main.py" (
    echo [ERROR] backend\main.py not found!
    pause
    exit /b 1
)

:: Check frontend build
if exist "%ROOT_DIR%frontend\dist\index.html" (
    echo [INFO] Production mode: http://localhost:8000
) else (
    echo [WARN] Frontend not built. API only mode.
    echo [WARN] To build frontend: cd frontend ^&^& npm run build
)
echo.

:: Start service
cd /d "%BACKEND_DIR%"
python main.py

pause
