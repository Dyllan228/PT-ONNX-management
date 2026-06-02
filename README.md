# PT-ONNX Benchmark Tool v2.0

A visual comparison tool for object detection models. Supports PyTorch/ONNX model management, conversion, inference visualization, and performance comparison.

[中文文档](README_zh.md)

## Quick Start

### Development Mode

> Requires: Python 3.8+ AND Node.js 16+

```bash
# 1. Setup environment (first time only)
setup.bat

# 2. Start backend + frontend
start-dev.bat

# 3. Open browser
http://localhost:5173
```

### Production Mode

> Requires: Python 3.8+ only (after frontend is built)

```bash
# 1. Setup environment (first time only)
setup.bat

# 2. Build frontend (first time only, requires Node.js)
build-frontend.bat

# 3. Start service
start.bat

# 4. Open browser
http://localhost:8000
```

## Deploy to Another PC

### Option A: Online Deploy (target PC has internet)

Copy to target PC:
- `backend/` (entire folder)
- `frontend/` (entire folder)
- `setup.bat`
- `start.bat`
- `build-frontend.bat`

On target PC:
```bash
setup.bat           # Install dependencies
build-frontend.bat  # Build frontend
start.bat           # Start service
```

### Option B: Offline Deploy (target PC has no internet)

On dev PC:
```bash
pack-offline.bat    # Download all packages
build-frontend.bat  # Build frontend
```

Copy to target PC:
- `backend/`
- `frontend/dist/` (build output)
- `offline_packages/`
- `setup.bat`
- `start.bat`

On target PC:
```bash
setup.bat   # Install from offline packages
start.bat   # Start service
```

## Features

| Feature | Description |
|---------|-------------|
| Model Management | Upload .pt models, auto metadata extraction, PT→ONNX conversion |
| Dataset Management | Import YOLO ZIP datasets, auto class/statistics parsing |
| Inference Visualization | PT/ONNX support, CPU/GPU, image/video, real-time display |
| Performance Comparison | PT vs ONNX / PT vs PT / ONNX vs ONNX, speed/memory/FPS metrics |

## Tech Stack

- **Backend**: Python 3.8+, FastAPI, SQLAlchemy, SQLite, PyTorch, ONNX Runtime
- **Frontend**: Vue 3, Element Plus, Pinia, ECharts, Vite

## Project Structure

```
PT-ONNX-benchmark-v2.0/
├── setup.bat               # Environment setup
├── start.bat               # Start (production)
├── start-dev.bat           # Start (development)
├── build-frontend.bat      # Build frontend
├── pack-offline.bat        # Download offline packages
├── backend/
│   ├── main.py             # Entry point
│   ├── requirements.txt    # Full dependencies
│   ├── requirements-runtime.txt  # Runtime dependencies
│   ├── api/                # API routes
│   ├── services/           # Business logic
│   ├── engines/            # PT/ONNX engines
│   ├── db/                 # Database
│   ├── schemas/            # Pydantic models
│   └── tests/              # Unit tests
├── frontend/
│   ├── package.json
│   ├── src/                # Vue source
│   └── dist/               # Build output
└── storage/                # Runtime data (auto-created)
    ├── models/pt/          # PT models
    ├── models/onnx/        # ONNX models
    ├── datasets/           # Datasets
    ├── results/            # Inference results
    └── benchmark.db        # SQLite database
```

## Run Tests

```bash
cd backend
.venv\Scripts\activate
python -m pytest tests/ -v
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Python not found" | Install Python 3.8+, check "Add to PATH" |
| "No module named 'fastapi'" | Run `setup.bat` |
| "Frontend not built" | Run `build-frontend.bat` |
| "No module named 'ultralytics'" | Optional. Run `pip install ultralytics` for YOLO metadata |
| Port 8000 in use | Edit port in `backend/main.py` |
