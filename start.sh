#!/bin/bash
set -e

echo "========================================"
echo "  PT-ONNX Benchmark Tool v2.0"
echo "========================================"
echo ""

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

# Check virtualenv
if [ ! -f "$BACKEND_DIR/.venv/bin/activate" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "Please run ./setup.sh first."
    exit 1
fi

# Activate virtualenv
source "$BACKEND_DIR/.venv/bin/activate"

# Check main.py
if [ ! -f "$BACKEND_DIR/main.py" ]; then
    echo "[ERROR] backend/main.py not found!"
    exit 1
fi

# Check frontend
if [ -f "$ROOT_DIR/frontend/dist/index.html" ]; then
    echo "[INFO] Production mode: http://localhost:8000"
else
    echo "[WARN] Frontend not built. API only mode."
    echo "[WARN] To build frontend: cd frontend && npm run build"
fi
echo ""

# Start service
cd "$BACKEND_DIR"
python main.py
