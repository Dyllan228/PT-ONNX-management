@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   PT-ONNX Benchmark Tool v2.0
echo   Docker Build Script
echo ========================================
echo.

:: 检查 Docker
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker not found!
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

:: 检查 Docker 是否运行
docker info >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop.
    pause
    exit /b 1
)

echo [INFO] Building Docker image...
echo [INFO] This may take 10-20 minutes for the first build...
echo.

:: 构建镜像
docker build -t pt-onnx-benchmark:latest .

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build Successful!
echo ========================================
echo.
echo Image: pt-onnx-benchmark:latest
echo.
echo To run the container:
echo   docker-compose up -d
echo.
echo To save the image for transfer:
echo   docker save pt-onnx-benchmark:latest -o pt-onnx-benchmark.tar
echo.
pause
