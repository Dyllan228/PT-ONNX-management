@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   PT-ONNX Benchmark Tool v2.0
echo   Download Offline Packages
echo ========================================
echo.

set "ROOT_DIR=%~dp0"
set "PACK_DIR=%ROOT_DIR%offline_packages"

:: Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

:: Create directory
if not exist "%PACK_DIR%" mkdir "%PACK_DIR%"

:: Download PyTorch
echo [1/3] Downloading PyTorch (~800MB)...
echo       This may take 5-10 minutes...
echo.
pip download torch --index-url https://download.pytorch.org/whl/cpu -d "%PACK_DIR%"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to download PyTorch
    pause
    exit /b 1
)

:: Download other packages
echo.
echo [2/3] Downloading other packages...
pip download fastapi==0.115.0 uvicorn==0.30.0 sqlalchemy==2.0.35 pydantic==2.9.0 python-multipart==0.0.9 onnxruntime==1.19.0 onnx==1.17.0 opencv-python-headless==4.10.0.84 numpy==1.24.4 psutil==6.0.0 -d "%PACK_DIR%"

:: Done
echo.
echo [3/3] Download complete!
echo.
echo ========================================
echo   Offline packages saved to: offline_packages\
echo ========================================
echo.
echo To deploy on target machine:
echo   1. Copy these folders: backend\, frontend\dist\, offline_packages\
echo   2. Run setup.bat on target machine
echo   3. Run start.bat to start
echo.
pause
