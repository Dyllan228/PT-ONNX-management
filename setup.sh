#!/bin/bash
set -e

echo "========================================"
echo "  PT-ONNX Benchmark Tool v2.0"
echo "  Environment Setup Script"
echo "========================================"
echo ""

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Step 1: Check Python
echo "[1/5] Checking prerequisites..."
PYTHON=""
if command -v python3 &> /dev/null; then
    PYTHON="python3"
elif command -v python &> /dev/null; then
    PYTHON="python"
else
    echo "[ERROR] Python not found!"
    echo "Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
    echo "macOS: brew install python3"
    exit 1
fi
PY_VER=$($PYTHON --version 2>&1)
echo "[OK] $PY_VER"

# Step 2: Create virtual environment
echo ""
echo "[2/5] Setting up virtual environment..."
if [ ! -d "$ROOT_DIR/backend/.venv" ]; then
    $PYTHON -m venv "$ROOT_DIR/backend/.venv"
    echo "[OK] Virtual environment created"
else
    echo "[OK] Virtual environment already exists"
fi
source "$ROOT_DIR/backend/.venv/bin/activate"

# Step 3: Install PyTorch
echo ""
echo "[3/5] Installing PyTorch..."
if python -c "import torch" 2>/dev/null; then
    echo "[OK] PyTorch already installed"
else
    OFFLINE_DIR="$ROOT_DIR/offline_packages"
    if [ -d "$OFFLINE_DIR" ] && ls "$OFFLINE_DIR"/torch*.whl 1>/dev/null 2>&1; then
        echo "[INFO] Installing PyTorch from offline packages..."
        pip install --no-index --find-links="$OFFLINE_DIR" torch -q
    else
        echo "[INFO] Downloading PyTorch (CPU version, ~800MB)..."
        pip install torch --index-url https://download.pytorch.org/whl/cpu -q
    fi
    echo "[OK] PyTorch installed"
fi

# Step 4: Install other dependencies
echo ""
echo "[4/5] Installing other dependencies..."
OFFLINE_DIR="$ROOT_DIR/offline_packages"
if [ -d "$OFFLINE_DIR" ]; then
    echo "[INFO] Installing from offline packages..."
    pip install --no-index --find-links="$OFFLINE_DIR" fastapi uvicorn sqlalchemy pydantic python-multipart onnxruntime onnx opencv-python-headless numpy psutil -q
else
    echo "[INFO] Downloading from internet..."
    pip install -r "$ROOT_DIR/backend/requirements-runtime.txt" -q
fi
echo "[OK] Dependencies installed"

# Step 5: Create directories
echo ""
echo "[5/5] Creating storage directories..."
mkdir -p "$ROOT_DIR/storage/models/pt"
mkdir -p "$ROOT_DIR/storage/models/onnx"
mkdir -p "$ROOT_DIR/storage/datasets"
mkdir -p "$ROOT_DIR/storage/results"
echo "[OK] Directories created"

# Done
echo ""
echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "To start the application:"
echo "  ./start.sh"
echo ""
