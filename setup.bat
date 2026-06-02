@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   PT-ONNX Benchmark Tool v2.0
echo   Environment Setup Script
echo ========================================
echo.

:: ============================================
:: Step 1: Check prerequisites
:: ============================================
echo [1/5] Checking prerequisites...

:: Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    echo IMPORTANT: Check "Add Python to PATH" during installation
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo [OK] Python %PY_VER%

:: ============================================
:: Step 2: Create virtual environment
:: ============================================
echo.
echo [2/5] Setting up virtual environment...

if not exist "backend\.venv" (
    python -m venv backend\.venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

:: Activate
call backend\.venv\Scripts\activate.bat

:: ============================================
:: Step 3: Install PyTorch
:: ============================================
echo.
echo [3/5] Installing PyTorch...

python -c "import torch" >nul 2>nul
if %errorlevel% equ 0 (
    echo [OK] PyTorch already installed
) else (
    set "OFFLINE_DIR=%~dp0offline_packages"
    if exist "%OFFLINE_DIR%\torch*" (
        echo [INFO] Installing PyTorch from offline packages...
        pip install --no-index --find-links="%OFFLINE_DIR%" torch -q
    ) else (
        echo [INFO] Downloading PyTorch (CPU version, ~800MB)...
        echo [INFO] This may take 5-10 minutes...
        pip install torch --index-url https://download.pytorch.org/whl/cpu -q
    )
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install PyTorch
        pause
        exit /b 1
    )
    echo [OK] PyTorch installed
)

:: ============================================
:: Step 4: Install other dependencies
:: ============================================
echo.
echo [4/5] Installing other dependencies...

set "OFFLINE_DIR=%~dp0offline_packages"
if exist "%OFFLINE_DIR%" (
    echo [INFO] Installing from offline packages...
    pip install --no-index --find-links="%OFFLINE_DIR%" fastapi uvicorn sqlalchemy pydantic python-multipart onnxruntime onnx opencv-python-headless numpy psutil -q
) else (
    echo [INFO] Downloading from internet...
    pip install -r backend\requirements-runtime.txt -q
)
echo [OK] Dependencies installed

:: ============================================
:: Step 5: Create directories
:: ============================================
echo.
echo [5/5] Creating storage directories...

if not exist "storage" mkdir storage
if not exist "storage\models\pt" mkdir storage\models\pt
if not exist "storage\models\onnx" mkdir storage\models\onnx
if not exist "storage\datasets" mkdir storage\datasets
if not exist "storage\results" mkdir storage\results
echo [OK] Directories created

:: ============================================
:: Done
:: ============================================
echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo To start the application:
echo   - Production mode: start.bat
echo   - Development mode: start-dev.bat
echo.
pause
