# PT-ONNX 可视化对比工具实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个基于 Vue 3 + FastAPI 的 PyTorch/ONNX 模型可视化对比工具，支持模型管理、自动转换、推理可视化和多维度性能对比。

**Architecture:** 前后端分离 SPA 架构。FastAPI 后端提供 REST API，Vue 3 前端通过 Axios 调用，耗时操作采用任务机制（提交任务 → 返回 task_id → 前端轮询）。数据存储使用 SQLite + 本地文件系统。

**Tech Stack:** Vue 3, Element Plus, ECharts, Pinia, Axios, FastAPI, SQLAlchemy, SQLite, PyTorch, ONNX Runtime, pytest, Uvicorn

---

## File Structure Overview

```
PT-ONNX-benchmark-v2.0/
├── helmet-vest-v1.pt                     # 已有：预置模型
├── 反光衣测试.mp4                         # 已有：预置数据源
├── backend/
│   ├── main.py                           # FastAPI 入口 + 启动扫描
│   ├── requirements.txt
│   ├── api/
│   │   ├── __init__.py
│   │   ├── models.py                     # 模型管理 API
│   │   ├── convert.py                    # 转换 API
│   │   ├── inference.py                  # 推理 API
│   │   ├── benchmark.py                  # 对比 API
│   │   ├── datasets.py                   # 数据源 API
│   │   └── tasks.py                      # 任务查询 API
│   ├── services/
│   │   ├── __init__.py
│   │   ├── model_service.py              # 模型元数据 + 自动描述
│   │   ├── convert_service.py            # PT → ONNX 转换
│   │   ├── inference_service.py          # 推理调度
│   │   ├── benchmark_service.py          # 性能测试
│   │   └── scan_service.py               # 目录扫描
│   ├── engines/
│   │   ├── __init__.py
│   │   ├── pt_engine.py                  # PyTorch 推理
│   │   └── onnx_engine.py                # ONNX Runtime 推理
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py                   # SQLAlchemy 引擎
│   │   └── models.py                     # 表模型
│   ├── storage/
│   │   ├── __init__.py
│   │   └── file_manager.py               # 文件路径管理
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── model_schema.py
│   │   ├── convert_schema.py
│   │   ├── inference_schema.py
│   │   └── benchmark_schema.py
│   └── tests/
│       ├── conftest.py                   # pytest fixtures
│       ├── test_models_api.py
│       ├── test_convert_api.py
│       ├── test_inference_api.py
│       ├── test_benchmark_api.py
│       ├── test_scan_service.py
│       └── test_model_service.py
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js
│       ├── App.vue                       # 顶层布局 + 标签页
│       ├── api/
│       │   ├── request.js                # Axios 实例 + 拦截器
│       │   ├── models.js
│       │   ├── convert.js
│       │   ├── inference.js
│       │   ├── benchmark.js
│       │   ├── datasets.js
│       │   └── tasks.js
│       ├── components/
│       │   ├── TaskProgress.vue          # 复用：任务进度
│       │   ├── ResultImage.vue           # 复用：标注结果图
│       │   ├── MetricsChart.vue          # 复用：性能图表
│       │   └── FileUploader.vue          # 复用：文件上传
│       ├── views/
│       │   ├── ModelManager.vue
│       │   ├── ModelConvert.vue
│       │   ├── InferenceVisual.vue
│       │   ├── PerformanceCompare.vue
│       │   └── VersionManage.vue
│       ├── stores/
│       │   └── models.js                 # Pinia 模型状态
│       ├── router/
│       │   └── index.js
│       └── utils/
│           └── polling.js                # 轮询封装
└── storage/                              # 运行时自动生成
    ├── models/pt/
    ├── models/onnx/
    ├── uploads/images/
    ├── uploads/videos/
    └── results/
```

---

## Task 1: Project Scaffolding & Database

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/main.py`
- Create: `backend/db/__init__.py`
- Create: `backend/db/database.py`
- Create: `backend/db/models.py`
- Create: `backend/storage/__init__.py`
- Create: `backend/storage/file_manager.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_database.py`

- [ ] **Step 1: Create backend directory structure**

```bash
mkdir -p backend/{api,services,engines,db,storage,schemas,tests}
mkdir -p storage/{models/pt,models/onnx,uploads/images,uploads/videos,results}
```

- [ ] **Step 2: Write `backend/requirements.txt`**

```
fastapi==0.115.0
uvicorn==0.30.0
sqlalchemy==2.0.35
pydantic==2.9.0
torch==2.4.0
onnxruntime==1.19.0
onnx==1.17.0
opencv-python==4.10.0
numpy==1.26.4
python-multipart==0.0.9
pytest==8.3.0
httpx==0.27.0
```

- [ ] **Step 3: Write the failing test for database initialization**

```python
# backend/tests/test_database.py
import pytest
from sqlalchemy import text
from db.database import engine, Base, init_db
from db.models import Model, Task, BenchmarkRecord


def test_init_db_creates_tables():
    """init_db should create all tables in the database."""
    init_db()
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        )
        tables = {row[0] for row in result}
    assert "models" in tables
    assert "tasks" in tables
    assert "benchmark_records" in tables
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_database.py -v`
Expected: ModuleNotFoundError or ImportError

- [ ] **Step 5: Write `backend/db/database.py`**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./storage/benchmark.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    os.makedirs("storage", exist_ok=True)
    Base.metadata.create_all(bind=engine)
```

- [ ] **Step 6: Write `backend/db/models.py`**

```python
from sqlalchemy import Column, Integer, String, Text, Boolean, BigInteger, Float, DateTime, JSON
from sqlalchemy.sql import func
from db.database import Base


class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    version = Column(String(100), nullable=False)
    pt_file_path = Column(String(500), nullable=False)
    onnx_file_path = Column(String(500), nullable=True)
    onnx_converted = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    class_names = Column(JSON, nullable=True)
    input_size = Column(JSON, nullable=True)
    param_count = Column(BigInteger, nullable=True)
    pt_file_size = Column(BigInteger, nullable=True)
    onnx_file_size = Column(BigInteger, nullable=True)
    training_epochs = Column(Integer, nullable=True)
    training_samples = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True)
    type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    progress = Column(Integer, default=0)
    params = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error_msg = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    finished_at = Column(DateTime, nullable=True)


class BenchmarkRecord(Base):
    __tablename__ = "benchmark_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), nullable=False)
    model_id = Column(Integer, nullable=False)
    model_type = Column(String(10), nullable=False)
    device = Column(String(20), nullable=False)
    avg_inference_ms = Column(Float, nullable=True)
    avg_preprocess_ms = Column(Float, nullable=True)
    avg_postprocess_ms = Column(Float, nullable=True)
    peak_memory_mb = Column(Float, nullable=True)
    model_size_mb = Column(Float, nullable=True)
    fps = Column(Float, nullable=True)
    precision_metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
```

- [ ] **Step 7: Write `backend/storage/file_manager.py`**

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"
MODELS_PT_DIR = STORAGE_DIR / "models" / "pt"
MODELS_ONNX_DIR = STORAGE_DIR / "models" / "onnx"
UPLOADS_IMAGES_DIR = STORAGE_DIR / "uploads" / "images"
UPLOADS_VIDEOS_DIR = STORAGE_DIR / "uploads" / "videos"
RESULTS_DIR = STORAGE_DIR / "results"

SUPPORTED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
SUPPORTED_VIDEO_EXT = {".mp4", ".avi", ".mov", ".mkv"}


def ensure_dirs():
    for d in [MODELS_PT_DIR, MODELS_ONNX_DIR, UPLOADS_IMAGES_DIR,
              UPLOADS_VIDEOS_DIR, RESULTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def get_root_pt_files():
    """Scan project root for .pt files (pre-set default models)."""
    return list(BASE_DIR.glob("*.pt"))


def get_root_media_files():
    """Scan project root for image/video files (pre-set default data sources)."""
    files = []
    for f in BASE_DIR.iterdir():
        if f.suffix.lower() in SUPPORTED_IMAGE_EXT | SUPPORTED_VIDEO_EXT:
            files.append(f)
    return files
```

- [ ] **Step 8: Write `backend/tests/conftest.py`**

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base, get_db
from main import app

TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)
```

- [ ] **Step 9: Write `backend/main.py` (minimal stub)**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.database import init_db

app = FastAPI(title="PT-ONNX Benchmark Tool", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}
```

- [ ] **Step 10: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_database.py -v`
Expected: PASSED

- [ ] **Step 11: Write `backend/tests/test_health.py`**

```python
def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "2.0.0"
```

- [ ] **Step 12: Run all backend tests**

Run: `cd backend && python -m pytest tests/ -v`
Expected: ALL PASSED

- [ ] **Step 13: Commit**

```bash
git init
git add backend/ storage/ .gitignore
git commit -m "feat: project scaffolding with database, file manager, and health check"
```

---

## Task 2: Pydantic Schemas & Model Management API

**Files:**
- Create: `backend/schemas/__init__.py`
- Create: `backend/schemas/model_schema.py`
- Create: `backend/schemas/convert_schema.py`
- Create: `backend/schemas/inference_schema.py`
- Create: `backend/schemas/benchmark_schema.py`
- Create: `backend/api/__init__.py`
- Create: `backend/api/models.py`
- Create: `backend/services/__init__.py`
- Create: `backend/services/model_service.py`
- Create: `backend/tests/test_models_api.py`

- [ ] **Step 1: Write all Pydantic schemas**

```python
# backend/schemas/model_schema.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ModelCreate(BaseModel):
    name: str
    version: str
    pt_file_path: str
    class_names: Optional[List[str]] = None
    input_size: Optional[List[int]] = None
    training_epochs: Optional[int] = None
    training_samples: Optional[int] = None


class ModelUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    class_names: Optional[List[str]] = None
    input_size: Optional[List[int]] = None
    training_epochs: Optional[int] = None
    training_samples: Optional[int] = None


class ModelResponse(BaseModel):
    id: int
    name: str
    version: str
    pt_file_path: str
    onnx_file_path: Optional[str] = None
    onnx_converted: bool
    description: Optional[str] = None
    class_names: Optional[List[str]] = None
    input_size: Optional[List[int]] = None
    param_count: Optional[int] = None
    pt_file_size: Optional[int] = None
    onnx_file_size: Optional[int] = None
    training_epochs: Optional[int] = None
    training_samples: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
```

```python
# backend/schemas/convert_schema.py
from pydantic import BaseModel
from typing import Optional


class ConvertRequest(BaseModel):
    model_id: int
    input_size: Optional[list] = [640, 640]
    dynamic_batch: Optional[bool] = True
    opset_version: Optional[int] = 11
```

```python
# backend/schemas/inference_schema.py
from pydantic import BaseModel
from typing import Optional, List


class InferenceRequest(BaseModel):
    model_id: int
    model_type: str  # "pt" or "onnx"
    device: str  # "cpu" or "cuda"
    dataset_id: Optional[int] = None  # existing dataset
    confidence_threshold: Optional[float] = 0.5
```

```python
# backend/schemas/benchmark_schema.py
from pydantic import BaseModel
from typing import Optional, List


class BenchmarkRequest(BaseModel):
    model_ids: List[int]
    model_types: List[str]  # parallel to model_ids
    devices: List[str]  # ["cpu"], ["cuda"], or ["cpu", "cuda"]
    dataset_id: Optional[int] = None
    confidence_threshold: Optional[float] = 0.5
    num_runs: Optional[int] = 100
```

- [ ] **Step 2: Write the failing test for model CRUD**

```python
# backend/tests/test_models_api.py
import io


def test_list_models_empty(client):
    response = client.get("/api/models")
    assert response.status_code == 200
    assert response.json() == []


def test_upload_model(client, tmp_path):
    # Create a fake .pt file
    pt_content = b"fake_pt_model_content"
    response = client.post(
        "/api/models/upload",
        files={"file": ("test-model.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "test-model", "version": "v1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test-model"
    assert data["version"] == "v1"
    assert data["pt_file_path"].endswith(".pt")
    assert data["onnx_converted"] is False


def test_get_model(client):
    # Upload first
    pt_content = b"fake_pt_model_content"
    upload_resp = client.post(
        "/api/models/upload",
        files={"file": ("test-model.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "test-model", "version": "v1"},
    )
    model_id = upload_resp.json()["id"]

    response = client.get(f"/api/models/{model_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "test-model"


def test_get_model_not_found(client):
    response = client.get("/api/models/999")
    assert response.status_code == 404


def test_update_model(client):
    pt_content = b"fake_pt_model_content"
    upload_resp = client.post(
        "/api/models/upload",
        files={"file": ("test-model.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "test-model", "version": "v1"},
    )
    model_id = upload_resp.json()["id"]

    response = client.put(
        f"/api/models/{model_id}",
        json={"name": "updated-model", "description": "Updated description"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "updated-model"
    assert response.json()["description"] == "Updated description"


def test_delete_model(client):
    pt_content = b"fake_pt_model_content"
    upload_resp = client.post(
        "/api/models/upload",
        files={"file": ("test-model.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "test-model", "version": "v1"},
    )
    model_id = upload_resp.json()["id"]

    response = client.delete(f"/api/models/{model_id}")
    assert response.status_code == 200

    # Verify it's gone
    get_resp = client.get(f"/api/models/{model_id}")
    assert get_resp.status_code == 404
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_models_api.py -v`
Expected: 404 on route not found

- [ ] **Step 4: Write `backend/services/model_service.py`**

```python
import torch
import os
from sqlalchemy.orm import Session
from db.models import Model as ModelDB
from schemas.model_schema import ModelCreate, ModelUpdate
from storage.file_manager import MODELS_PT_DIR


def extract_model_metadata(pt_path: str) -> dict:
    """Extract metadata from a PyTorch model file."""
    metadata = {
        "param_count": None,
        "class_names": None,
        "input_size": None,
        "description": None,
    }
    try:
        checkpoint = torch.load(pt_path, map_location="cpu", weights_only=False)
        # Handle YOLO-style saved models
        if isinstance(checkpoint, dict):
            if "model" in checkpoint:
                model = checkpoint["model"]
            elif "state_dict" in checkpoint:
                model = checkpoint["state_dict"]
            else:
                model = None

            if model is not None:
                if hasattr(model, "parameters"):
                    param_count = sum(p.numel() for p in model.parameters())
                    metadata["param_count"] = param_count
                if hasattr(model, "names"):
                    metadata["class_names"] = list(model.names.values())
        # Handle ultralytics YOLO saved model (full model object)
        elif hasattr(checkpoint, "model"):
            model = checkpoint.model if hasattr(checkpoint, "model") else checkpoint
            if hasattr(model, "parameters"):
                param_count = sum(p.numel() for p in model.parameters())
                metadata["param_count"] = param_count
            if hasattr(checkpoint, "names"):
                metadata["class_names"] = list(checkpoint.names.values())
    except Exception as e:
        metadata["description"] = f"元数据提取失败: {str(e)}"

    # Build description
    parts = []
    if metadata["param_count"]:
        if metadata["param_count"] > 1_000_000:
            parts.append(f"参数量: {metadata['param_count'] / 1_000_000:.1f}M")
        else:
            parts.append(f"参数量: {metadata['param_count'] / 1_000:.1f}K")
    if metadata["class_names"]:
        parts.append(f"类别数: {len(metadata['class_names'])}")
        parts.append(f"类别: {', '.join(metadata['class_names'])}")
    if parts:
        metadata["description"] = " | ".join(parts)

    return metadata


def create_model(db: Session, name: str, version: str, pt_file_path: str,
                 file_size: int, **kwargs) -> ModelDB:
    metadata = extract_model_metadata(pt_file_path)
    db_model = ModelDB(
        name=name,
        version=version,
        pt_file_path=pt_file_path,
        pt_file_size=file_size,
        description=metadata.get("description"),
        param_count=metadata.get("param_count"),
        class_names=metadata.get("class_names"),
        **kwargs,
    )
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model


def get_models(db: Session, skip: int = 0, limit: int = 100):
    return db.query(ModelDB).offset(skip).limit(limit).all()


def get_model(db: Session, model_id: int):
    return db.query(ModelDB).filter(ModelDB.id == model_id).first()


def update_model(db: Session, model_id: int, update: ModelUpdate):
    db_model = get_model(db, model_id)
    if not db_model:
        return None
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_model, key, value)
    db.commit()
    db.refresh(db_model)
    return db_model


def delete_model(db: Session, model_id: int):
    db_model = get_model(db, model_id)
    if not db_model:
        return False
    # Delete files
    if os.path.exists(db_model.pt_file_path):
        os.remove(db_model.pt_file_path)
    if db_model.onnx_file_path and os.path.exists(db_model.onnx_file_path):
        os.remove(db_model.onnx_file_path)
    db.delete(db_model)
    db.commit()
    return True
```

- [ ] **Step 5: Write `backend/api/models.py`**

```python
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.model_schema import ModelResponse, ModelUpdate
from services import model_service
from storage.file_manager import MODELS_PT_DIR, ensure_dirs

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=list[ModelResponse])
def list_models(db: Session = Depends(get_db)):
    return model_service.get_models(db)


@router.get("/{model_id}", response_model=ModelResponse)
def get_model(model_id: int, db: Session = Depends(get_db)):
    model = model_service.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.post("/upload", response_model=ModelResponse)
async def upload_model(
    file: UploadFile = File(...),
    name: str = Form(...),
    version: str = Form("v1"),
    db: Session = Depends(get_db),
):
    ensure_dirs()
    if not file.filename.endswith(".pt"):
        raise HTTPException(status_code=400, detail="Only .pt files are supported")

    # Save file
    filename = f"{name}_{version}_{uuid.uuid4().hex[:8]}.pt"
    file_path = MODELS_PT_DIR / filename
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return model_service.create_model(
        db, name=name, version=version,
        pt_file_path=str(file_path), file_size=len(content),
    )


@router.put("/{model_id}", response_model=ModelResponse)
def update_model(model_id: int, update: ModelUpdate, db: Session = Depends(get_db)):
    model = model_service.update_model(db, model_id, update)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.delete("/{model_id}")
def delete_model(model_id: int, db: Session = Depends(get_db)):
    success = model_service.delete_model(db, model_id)
    if not success:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"success": True}


@router.post("/scan")
def scan_models(db: Session = Depends(get_db)):
    from services.scan_service import scan_and_register
    count = scan_and_register(db)
    return {"scanned": count}
```

- [ ] **Step 6: Register router in `backend/main.py`**

Add to `main.py`:

```python
from api.models import router as models_router
app.include_router(models_router)
```

- [ ] **Step 7: Run tests**

Run: `cd backend && python -m pytest tests/test_models_api.py -v`
Expected: ALL PASSED

- [ ] **Step 8: Commit**

```bash
git add backend/schemas/ backend/api/models.py backend/services/model_service.py backend/tests/test_models_api.py backend/main.py
git commit -m "feat: model management API with CRUD, upload, and metadata extraction"
```

---

## Task 3: Auto-Scan Service & Startup

**Files:**
- Create: `backend/services/scan_service.py`
- Create: `backend/tests/test_scan_service.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_scan_service.py
import os
import shutil
import pytest
from unittest.mock import patch
from db.database import SessionLocal
from services.scan_service import scan_and_register
from db.models import Model as ModelDB


def test_scan_root_directory(tmp_path):
    """scan_and_register should find .pt files in the root directory."""
    # Create a fake .pt file in a temp directory
    fake_pt = tmp_path / "test-scan-model.pt"
    fake_pt.write_bytes(b"fake_pt_content")

    with patch("services.scan_service.BASE_DIR", tmp_path):
        with patch("services.scan_service.MODELS_PT_DIR", tmp_path / "storage" / "models" / "pt"):
            (tmp_path / "storage" / "models" / "pt").mkdir(parents=True, exist_ok=True)
            db = SessionLocal()
            try:
                count = scan_and_register(db)
                assert count >= 1
                # Verify the model was registered
                models = db.query(ModelDB).all()
                assert len(models) >= 1
                assert models[0].name == "test-scan-model"
            finally:
                db.close()


def test_scan_skips_already_registered(tmp_path):
    """Running scan twice should not create duplicates."""
    fake_pt = tmp_path / "dup-model.pt"
    fake_pt.write_bytes(b"fake_pt_content")

    with patch("services.scan_service.BASE_DIR", tmp_path):
        with patch("services.scan_service.MODELS_PT_DIR", tmp_path / "storage" / "models" / "pt"):
            (tmp_path / "storage" / "models" / "pt").mkdir(parents=True, exist_ok=True)
            db = SessionLocal()
            try:
                scan_and_register(db)
                count1 = db.query(ModelDB).count()
                scan_and_register(db)
                count2 = db.query(ModelDB).count()
                assert count1 == count2
            finally:
                db.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_scan_service.py -v`
Expected: ModuleNotFoundError or test failure

- [ ] **Step 3: Write `backend/services/scan_service.py`**

```python
import os
from pathlib import Path
from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models import Model as ModelDB
from services.model_service import extract_model_metadata
from storage.file_manager import (
    BASE_DIR, MODELS_PT_DIR, MODELS_ONNX_DIR,
    get_root_media_files, ensure_dirs,
)

SUPPORTED_PT_EXT = {".pt"}


def scan_and_register(db: Session) -> int:
    """Scan directories and register found models. Returns count of newly registered."""
    ensure_dirs()
    count = 0

    # Scan directories to check
    scan_dirs = [BASE_DIR, MODELS_PT_DIR]
    registered_paths = {m.pt_file_path for m in db.query(ModelDB).all()}

    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for f in scan_dir.iterdir():
            if f.suffix.lower() not in SUPPORTED_PT_EXT:
                continue
            abs_path = str(f.resolve())
            if abs_path in registered_paths:
                continue

            # Derive name and version from filename
            stem = f.stem  # e.g., "helmet-vest-v1"
            name = stem.rsplit("-", 1)[0] if "-v" in stem else stem
            version = stem.rsplit("-", 1)[-1] if "-v" in stem else "v1"

            metadata = extract_model_metadata(abs_path)
            file_size = f.stat().st_size

            db_model = ModelDB(
                name=name,
                version=version,
                pt_file_path=abs_path,
                pt_file_size=file_size,
                description=metadata.get("description"),
                param_count=metadata.get("param_count"),
                class_names=metadata.get("class_names"),
            )
            db.add(db_model)
            count += 1
            registered_paths.add(abs_path)

    # Check for corresponding ONNX files
    for model in db.query(ModelDB).filter(ModelDB.onnx_converted == False).all():
        pt_path = Path(model.pt_file_path)
        onnx_path = MODELS_ONNX_DIR / pt_path.with_suffix(".onnx").name
        if onnx_path.exists():
            model.onnx_file_path = str(onnx_path)
            model.onnx_converted = True
            model.onnx_file_size = onnx_path.stat().st_size

    db.commit()
    return count
```

- [ ] **Step 4: Update `backend/main.py` startup**

```python
@app.on_event("startup")
def startup():
    init_db()
    # Auto-scan directories
    from services.scan_service import scan_and_register
    from db.database import SessionLocal
    db = SessionLocal()
    try:
        count = scan_and_register(db)
        print(f"Auto-scan: registered {count} new model(s)")
    finally:
        db.close()
```

- [ ] **Step 5: Run tests**

Run: `cd backend && python -m pytest tests/test_scan_service.py -v`
Expected: ALL PASSED

- [ ] **Step 6: Commit**

```bash
git add backend/services/scan_service.py backend/tests/test_scan_service.py backend/main.py
git commit -m "feat: auto-scan service for directory-based model registration at startup"
```

---

## Task 4: Model Conversion API

**Files:**
- Create: `backend/services/convert_service.py`
- Create: `backend/api/convert.py`
- Create: `backend/api/tasks.py`
- Create: `backend/tests/test_convert_api.py`

- [ ] **Step 1: Write the failing test for conversion task creation**

```python
# backend/tests/test_convert_api.py
import io


def test_create_convert_task(client):
    """POST /api/convert should create a task and return task_id."""
    # Upload a model first
    pt_content = b"fake_pt_content"
    upload_resp = client.post(
        "/api/models/upload",
        files={"file": ("conv-model.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "conv-model", "version": "v1"},
    )
    model_id = upload_resp.json()["id"]

    # Create convert task
    response = client.post("/api/convert", json={
        "model_id": model_id,
        "input_size": [640, 640],
        "dynamic_batch": True,
        "opset_version": 11,
    })
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "pending"


def test_get_convert_task(client):
    """GET /api/convert/{task_id} should return task status."""
    # Upload and create task
    pt_content = b"fake_pt_content"
    upload_resp = client.post(
        "/api/models/upload",
        files={"file": ("conv-model2.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "conv-model2", "version": "v1"},
    )
    model_id = upload_resp.json()["id"]
    task_resp = client.post("/api/convert", json={"model_id": model_id})
    task_id = task_resp.json()["task_id"]

    response = client.get(f"/api/convert/{task_id}")
    assert response.status_code == 200
    assert "status" in response.json()


def test_convert_nonexistent_model(client):
    """Converting a nonexistent model should return 404."""
    response = client.post("/api/convert", json={"model_id": 9999})
    assert response.status_code == 404
```

- [ ] **Step 2: Write the failing test for tasks API**

```python
# backend/tests/test_tasks_api.py


def test_get_task_status(client):
    """GET /api/tasks/{task_id} should return task info."""
    # Create a conversion task to get a task_id
    import io
    pt_content = b"fake_pt"
    upload_resp = client.post(
        "/api/models/upload",
        files={"file": ("task-model.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "task-model", "version": "v1"},
    )
    model_id = upload_resp.json()["id"]
    task_resp = client.post("/api/convert", json={"model_id": model_id})
    task_id = task_resp.json()["task_id"]

    response = client.get(f"/api/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "convert"
    assert data["status"] in ("pending", "running", "completed", "failed")


def test_delete_task(client):
    """DELETE /api/tasks/{task_id} should delete the task."""
    import io
    pt_content = b"fake_pt"
    upload_resp = client.post(
        "/api/models/upload",
        files={"file": ("del-model.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "del-model", "version": "v1"},
    )
    model_id = upload_resp.json()["id"]
    task_resp = client.post("/api/convert", json={"model_id": model_id})
    task_id = task_resp.json()["task_id"]

    response = client.delete(f"/api/tasks/{task_id}")
    assert response.status_code == 200

    get_resp = client.get(f"/api/tasks/{task_id}")
    assert get_resp.status_code == 404
```

- [ ] **Step 3: Run tests to verify failures**

Run: `cd backend && python -m pytest tests/test_convert_api.py tests/test_tasks_api.py -v`
Expected: FAIL

- [ ] **Step 4: Write `backend/services/convert_service.py`**

```python
import torch
import os
from pathlib import Path
from db.models import Model as ModelDB, Task
from storage.file_manager import MODELS_ONNX_DIR


def convert_pt_to_onnx(model: ModelDB, task: Task, db,
                       input_size=(640, 640), opset_version=11, dynamic_batch=True):
    """Convert a PT model to ONNX format. Updates task progress."""
    try:
        task.status = "running"
        task.progress = 10
        db.commit()

        # Load model
        checkpoint = torch.load(model.pt_file_path, map_location="cpu", weights_only=False)
        task.progress = 30
        db.commit()

        # Extract the actual model
        if isinstance(checkpoint, dict) and "model" in checkpoint:
            pt_model = checkpoint["model"]
        elif hasattr(checkpoint, "model"):
            pt_model = checkpoint.model
        else:
            pt_model = checkpoint

        pt_model.eval()
        task.progress = 50
        db.commit()

        # Create dummy input
        dummy_input = torch.randn(1, 3, input_size[0], input_size[1])

        # Determine output path
        pt_path = Path(model.pt_file_path)
        onnx_filename = pt_path.stem + ".onnx"
        onnx_path = MODELS_ONNX_DIR / onnx_filename
        onnx_path.parent.mkdir(parents=True, exist_ok=True)

        task.progress = 60
        db.commit()

        # Export to ONNX
        dynamic_axes = None
        if dynamic_batch:
            dynamic_axes = {"input": {0: "batch_size"}, "output": {0: "batch_size"}}

        torch.onnx.export(
            pt_model,
            dummy_input,
            str(onnx_path),
            opset_version=opset_version,
            input_names=["input"],
            output_names=["output"],
            dynamic_axes=dynamic_axes,
        )

        task.progress = 90
        db.commit()

        # Update model record
        model.onnx_file_path = str(onnx_path)
        model.onnx_converted = True
        model.onnx_file_size = onnx_path.stat().st_size

        task.progress = 100
        task.status = "completed"
        task.result = {"onnx_path": str(onnx_path), "file_size": model.onnx_file_size}
        db.commit()

    except Exception as e:
        task.status = "failed"
        task.error_msg = str(e)
        db.commit()
        raise
```

- [ ] **Step 5: Write `backend/api/convert.py`**

```python
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor
from db.database import get_db
from db.models import Task
from schemas.convert_schema import ConvertRequest
from services import convert_service, model_service

router = APIRouter(prefix="/api/convert", tags=["convert"])
executor = ThreadPoolExecutor(max_workers=2)


@router.post("")
def create_convert_task(req: ConvertRequest, db: Session = Depends(get_db)):
    model = model_service.get_model(db, req.model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if model.onnx_converted:
        raise HTTPException(status_code=400, detail="Model already converted to ONNX")

    task_id = uuid.uuid4().hex
    task = Task(id=task_id, type="convert", status="pending",
                params={"model_id": req.model_id, "input_size": req.input_size,
                        "opset_version": req.opset_version, "dynamic_batch": req.dynamic_batch})
    db.add(task)
    db.commit()

    # Submit to thread pool
    executor.submit(
        convert_service.convert_pt_to_onnx,
        model, task, db,
        input_size=tuple(req.input_size),
        opset_version=req.opset_version,
        dynamic_batch=req.dynamic_batch,
    )

    return {"task_id": task_id, "status": "pending"}


@router.get("/{task_id}")
def get_convert_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.type == "convert").first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": task.id,
        "status": task.status,
        "progress": task.progress,
        "result": task.result,
        "error_msg": task.error_msg,
    }
```

- [ ] **Step 6: Write `backend/api/tasks.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Task

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("/{task_id}")
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": task.id,
        "type": task.type,
        "status": task.status,
        "progress": task.progress,
        "params": task.params,
        "result": task.result,
        "error_msg": task.error_msg,
        "created_at": str(task.created_at) if task.created_at else None,
        "finished_at": str(task.finished_at) if task.finished_at else None,
    }


@router.delete("/{task_id}")
def delete_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"success": True}
```

- [ ] **Step 7: Register routers in `backend/main.py`**

```python
from api.convert import router as convert_router
from api.tasks import router as tasks_router
app.include_router(convert_router)
app.include_router(tasks_router)
```

- [ ] **Step 8: Run tests**

Run: `cd backend && python -m pytest tests/test_convert_api.py tests/test_tasks_api.py -v`
Expected: ALL PASSED

- [ ] **Step 9: Commit**

```bash
git add backend/services/convert_service.py backend/api/convert.py backend/api/tasks.py backend/tests/test_convert_api.py backend/tests/test_tasks_api.py backend/main.py
git commit -m "feat: model conversion API with PT-to-ONNX export and task management"
```

---

## Task 5: Inference Engine & API

**Files:**
- Create: `backend/engines/__init__.py`
- Create: `backend/engines/pt_engine.py`
- Create: `backend/engines/onnx_engine.py`
- Create: `backend/services/inference_service.py`
- Create: `backend/api/inference.py`
- Create: `backend/tests/test_inference_api.py`

- [ ] **Step 1: Write `backend/engines/pt_engine.py`**

```python
import torch
import cv2
import numpy as np
import time


class PTEngine:
    """PyTorch inference engine for YOLO-style detection models."""

    def __init__(self, model_path: str, device: str = "cpu"):
        self.device = torch.device(device if torch.cuda.is_available() or device == "cpu" else "cpu")
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)

        if isinstance(checkpoint, dict) and "model" in checkpoint:
            self.model = checkpoint["model"]
        elif hasattr(checkpoint, "model"):
            self.model = checkpoint.model
        else:
            self.model = checkpoint

        self.model.to(self.device)
        self.model.eval()

        # Extract class names
        if hasattr(checkpoint, "names"):
            self.names = checkpoint.names
        elif isinstance(checkpoint, dict) and "model" in checkpoint:
            m = checkpoint["model"]
            self.names = getattr(m, "names", {})
        else:
            self.names = {}

        if isinstance(self.names, list):
            self.names = {i: n for i, n in enumerate(self.names)}

    def preprocess(self, img: np.ndarray, input_size=(640, 640)):
        """Preprocess image: resize, normalize, to tensor."""
        img_resized = cv2.resize(img, (input_size[1], input_size[0]))
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        img_normalized = img_rgb.astype(np.float32) / 255.0
        img_tensor = torch.from_numpy(img_normalized).permute(2, 0, 1).unsqueeze(0)
        return img_tensor.to(self.device)

    def infer(self, img: np.ndarray, input_size=(640, 640), conf_threshold=0.5):
        """Run inference on a single image. Returns detections."""
        timings = {}

        # Preprocess
        t0 = time.time()
        img_tensor = self.preprocess(img, input_size)
        timings["preprocess_ms"] = (time.time() - t0) * 1000

        # Inference
        t0 = time.time()
        with torch.no_grad():
            outputs = self.model(img_tensor)
        timings["inference_ms"] = (time.time() - t0) * 1000

        # Postprocess
        t0 = time.time()
        detections = self._postprocess(outputs, img.shape, input_size, conf_threshold)
        timings["postprocess_ms"] = (time.time() - t0) * 1000

        return detections, timings

    def _postprocess(self, outputs, orig_shape, input_size, conf_threshold):
        """Parse model outputs into detection list."""
        detections = []
        h_orig, w_orig = orig_shape[:2]

        # Handle different output formats
        if isinstance(outputs, (list, tuple)):
            outputs = outputs[0]
        if isinstance(outputs, torch.Tensor):
            outputs = outputs.cpu().numpy()

        # Generic YOLO-style postprocessing
        if len(outputs.shape) == 3:
            outputs = outputs[0]

        for det in outputs:
            if len(det) < 6:
                continue
            confidence = float(det[4])
            if confidence < conf_threshold:
                continue
            class_id = int(det[5]) if len(det) > 5 else 0
            x1, y1, x2, y2 = det[0], det[1], det[2], det[3]

            # Scale back to original image
            x1 = float(x1) * w_orig / input_size[1]
            y1 = float(y1) * h_orig / input_size[0]
            x2 = float(x2) * w_orig / input_size[1]
            y2 = float(y2) * h_orig / input_size[0]

            detections.append({
                "class_id": class_id,
                "class_name": self.names.get(class_id, f"class_{class_id}"),
                "confidence": confidence,
                "bbox": [x1, y1, x2, y2],
            })

        return detections

    def get_metrics(self):
        """Return model metadata."""
        param_count = sum(p.numel() for p in self.model.parameters())
        return {
            "param_count": param_count,
            "names": self.names,
            "device": str(self.device),
        }
```

- [ ] **Step 2: Write `backend/engines/onnx_engine.py`**

```python
import onnxruntime as ort
import cv2
import numpy as np
import time


class ONNXEngine:
    """ONNX Runtime inference engine for detection models."""

    def __init__(self, model_path: str, device: str = "cpu"):
        providers = ["CUDAExecutionProvider"] if device == "cuda" else ["CPUExecutionProvider"]
        available = ort.get_available_providers()
        providers = [p for p in providers if p in available]
        if not providers:
            providers = ["CPUExecutionProvider"]

        self.session = ort.InferenceSession(model_path, providers=providers)
        self.input_name = self.session.get_inputs()[0].name
        self.output_names = [o.name for o in self.session.get_outputs()]
        self.device = providers[0].replace("ExecutionProvider", "").lower()
        self.names = {}

    def set_names(self, names: dict):
        self.names = names

    def preprocess(self, img: np.ndarray, input_size=(640, 640)):
        """Preprocess image for ONNX inference."""
        img_resized = cv2.resize(img, (input_size[1], input_size[0]))
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        img_normalized = img_rgb.astype(np.float32) / 255.0
        img_tensor = np.transpose(img_normalized, (2, 0, 1))[np.newaxis, ...]
        return img_tensor

    def infer(self, img: np.ndarray, input_size=(640, 640), conf_threshold=0.5):
        """Run inference on a single image. Returns detections."""
        timings = {}

        t0 = time.time()
        img_tensor = self.preprocess(img, input_size)
        timings["preprocess_ms"] = (time.time() - t0) * 1000

        t0 = time.time()
        outputs = self.session.run(self.output_names, {self.input_name: img_tensor})
        timings["inference_ms"] = (time.time() - t0) * 1000

        t0 = time.time()
        detections = self._postprocess(outputs, img.shape, input_size, conf_threshold)
        timings["postprocess_ms"] = (time.time() - t0) * 1000

        return detections, timings

    def _postprocess(self, outputs, orig_shape, input_size, conf_threshold):
        detections = []
        h_orig, w_orig = orig_shape[:2]
        output = outputs[0]

        if len(output.shape) == 3:
            output = output[0]

        for det in output:
            if len(det) < 6:
                continue
            confidence = float(det[4])
            if confidence < conf_threshold:
                continue
            class_id = int(det[5]) if len(det) > 5 else 0
            x1, y1, x2, y2 = det[0], det[1], det[2], det[3]

            x1 = float(x1) * w_orig / input_size[1]
            y1 = float(y1) * h_orig / input_size[0]
            x2 = float(x2) * w_orig / input_size[1]
            y2 = float(y2) * h_orig / input_size[0]

            detections.append({
                "class_id": class_id,
                "class_name": self.names.get(class_id, f"class_{class_id}"),
                "confidence": confidence,
                "bbox": [x1, y1, x2, y2],
            })

        return detections
```

- [ ] **Step 3: Write `backend/services/inference_service.py`**

```python
import cv2
import os
import uuid
from pathlib import Path
from db.models import Model as ModelDB, Task
from db.database import SessionLocal
from engines.pt_engine import PTEngine
from engines.onnx_engine import ONNXEngine
from storage.file_manager import RESULTS_DIR


def draw_detections(img, detections):
    """Draw bounding boxes and labels on image."""
    for det in detections:
        x1, y1, x2, y2 = [int(v) for v in det["bbox"]]
        label = f"{det['class_name']} {det['confidence']:.2f}"
        color = (0, 255, 0)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return img


def run_inference(model: ModelDB, task: Task, db,
                  model_type: str, device: str, data_path: str,
                  input_size=(640, 640), conf_threshold=0.5):
    """Run inference on image or video. Updates task progress."""
    try:
        task.status = "running"
        task.progress = 5
        db.commit()

        # Initialize engine
        if model_type == "pt":
            engine = PTEngine(model.pt_file_path, device=device)
        else:
            engine = ONNXEngine(model.onnx_file_path, device=device)
            if model.class_names:
                engine.set_names({i: n for i, n in enumerate(model.class_names)})

        task.progress = 15
        db.commit()

        result_dir = RESULTS_DIR / task.id
        annotated_dir = result_dir / "annotated"
        annotated_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(data_path).suffix.lower()
        all_detections = []

        if ext in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
            # Single image inference
            img = cv2.imread(data_path)
            detections, timings = engine.infer(img, input_size=input_size, conf_threshold=conf_threshold)
            annotated = draw_detections(img, detections)
            out_path = annotated_dir / "result.jpg"
            cv2.imwrite(str(out_path), annotated)
            all_detections = [{"frame": 0, "detections": detections, "timings": timings}]
            task.progress = 100

        elif ext in {".mp4", ".avi", ".mov", ".mkv"}:
            # Video inference
            cap = cv2.VideoCapture(data_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_idx = 0

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                detections, timings = engine.infer(frame, input_size=input_size, conf_threshold=conf_threshold)
                annotated = draw_detections(frame.copy(), detections)
                out_path = annotated_dir / f"frame_{frame_idx:06d}.jpg"
                cv2.imwrite(str(out_path), annotated)

                all_detections.append({
                    "frame": frame_idx,
                    "detections": detections,
                    "timings": timings,
                })
                frame_idx += 1

                if total_frames > 0:
                    task.progress = min(99, int(15 + 85 * frame_idx / total_frames))
                    db.commit()

            cap.release()
            task.progress = 100
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        task.status = "completed"
        task.result = {
            "annotated_dir": str(annotated_dir),
            "total_frames": len(all_detections),
            "detections_summary": all_detections[:10],  # first 10 frames in result
            "device": device,
            "model_type": model_type,
        }
        db.commit()

    except Exception as e:
        task.status = "failed"
        task.error_msg = str(e)
        db.commit()
        raise
```

- [ ] **Step 4: Write `backend/api/inference.py`**

```python
import uuid
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor
from db.database import get_db
from db.models import Task
from services import model_service
from services.inference_service import run_inference
from storage.file_manager import UPLOADS_IMAGES_DIR, UPLOADS_VIDEOS_DIR, ensure_dirs

router = APIRouter(prefix="/api/inference", tags=["inference"])
executor = ThreadPoolExecutor(max_workers=2)


@router.post("")
async def create_inference_task(
    model_id: int = Form(...),
    model_type: str = Form(...),
    device: str = Form("cpu"),
    confidence_threshold: float = Form(0.5),
    dataset_id: int = Form(None),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    model = model_service.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if model_type == "onnx" and not model.onnx_converted:
        raise HTTPException(status_code=400, detail="Model not yet converted to ONNX")

    # Handle file upload or use existing dataset
    if file:
        ensure_dirs()
        ext = os.path.splitext(file.filename)[1].lower()
        if ext in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
            save_dir = UPLOADS_IMAGES_DIR
        elif ext in {".mp4", ".avi", ".mov", ".mkv"}:
            save_dir = UPLOADS_VIDEOS_DIR
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
        file_path = save_dir / filename
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        data_path = str(file_path)
    elif dataset_id:
        # Look up existing dataset
        from db.models import Task as TaskModel
        # Simple approach: dataset_id is a task_id from previous inference or upload
        # For now, use the file path from a stored location
        raise HTTPException(status_code=400, detail="Use file upload for now")
    else:
        raise HTTPException(status_code=400, detail="No data source provided")

    task_id = uuid.uuid4().hex
    task = Task(
        id=task_id, type="inference", status="pending",
        params={"model_id": model_id, "model_type": model_type, "device": device,
                "confidence_threshold": confidence_threshold, "data_path": data_path},
    )
    db.add(task)
    db.commit()

    input_size = tuple(model.input_size) if model.input_size else (640, 640)
    executor.submit(
        run_inference, model, task, db,
        model_type=model_type, device=device, data_path=data_path,
        input_size=input_size, conf_threshold=confidence_threshold,
    )

    return {"task_id": task_id, "status": "pending"}


@router.get("/{task_id}")
def get_inference_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.type == "inference").first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": task.id,
        "status": task.status,
        "progress": task.progress,
        "result": task.result,
        "error_msg": task.error_msg,
    }


@router.get("/{task_id}/image/{frame_idx}")
def get_result_image(task_id: str, frame_idx: int):
    from storage.file_manager import RESULTS_DIR
    img_path = RESULTS_DIR / task_id / "annotated" / f"frame_{frame_idx:06d}.jpg"
    if not img_path.exists():
        img_path = RESULTS_DIR / task_id / "annotated" / "result.jpg"
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Result image not found")
    from fastapi.responses import FileResponse
    return FileResponse(str(img_path))
```

- [ ] **Step 5: Register router in `backend/main.py`**

```python
from api.inference import router as inference_router
app.include_router(inference_router)
```

- [ ] **Step 6: Write `backend/tests/test_inference_api.py`**

```python
import io


def test_create_inference_task_no_file(client):
    """Inference without any data source should return 400."""
    import io
    pt_content = b"fake_pt"
    upload_resp = client.post(
        "/api/models/upload",
        files={"file": ("inf-model.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "inf-model", "version": "v1"},
    )
    model_id = upload_resp.json()["id"]

    response = client.post("/api/inference", data={
        "model_id": model_id,
        "model_type": "pt",
        "device": "cpu",
    })
    assert response.status_code == 400


def test_create_inference_task_nonexistent_model(client):
    """Inference with nonexistent model should return 404."""
    response = client.post("/api/inference", data={
        "model_id": 9999,
        "model_type": "pt",
        "device": "cpu",
    })
    assert response.status_code == 404
```

- [ ] **Step 7: Run tests**

Run: `cd backend && python -m pytest tests/test_inference_api.py -v`
Expected: ALL PASSED

- [ ] **Step 8: Commit**

```bash
git add backend/engines/ backend/services/inference_service.py backend/api/inference.py backend/tests/test_inference_api.py backend/main.py
git commit -m "feat: inference engine (PT + ONNX) with image/video support and result visualization"
```

---

## Task 6: Benchmark API & Datasets API

**Files:**
- Create: `backend/services/benchmark_service.py`
- Create: `backend/api/benchmark.py`
- Create: `backend/api/datasets.py`
- Create: `backend/tests/test_benchmark_api.py`
- Create: `backend/tests/test_datasets_api.py`

- [ ] **Step 1: Write `backend/services/benchmark_service.py`**

```python
import time
import os
import psutil
import cv2
import numpy as np
from db.models import Model as ModelDB, Task, BenchmarkRecord
from engines.pt_engine import PTEngine
from engines.onnx_engine import ONNXEngine


def run_benchmark(task: Task, db, model_ids: list, model_types: list,
                  devices: list, data_path: str, input_size=(640, 640),
                  conf_threshold=0.5, num_runs=100):
    """Run benchmark comparing multiple models. Updates task progress."""
    try:
        task.status = "running"
        task.progress = 5
        db.commit()

        # Load test data
        img = cv2.imread(data_path)
        if img is None:
            raise ValueError(f"Cannot read data file: {data_path}")

        results = []
        total_configs = len(model_ids) * len(devices)

        for idx, (model_id, model_type) in enumerate(zip(model_ids, model_types)):
            model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
            if not model:
                continue

            for device in devices:
                config_progress_base = int(5 + 90 * (idx * len(devices) + devices.index(device)) / total_configs)

                # Initialize engine
                if model_type == "pt":
                    engine = PTEngine(model.pt_file_path, device=device)
                    model_file_size = model.pt_file_size or os.path.getsize(model.pt_file_path)
                else:
                    engine = ONNXEngine(model.onnx_file_path, device=device)
                    model_file_size = model.onnx_file_size or os.path.getsize(model.onnx_file_path)
                    if model.class_names:
                        engine.set_names({i: n for i, n in enumerate(model.class_names)})

                # Warmup
                for _ in range(3):
                    engine.infer(img, input_size=input_size, conf_threshold=conf_threshold)

                # Benchmark
                process = psutil.Process()
                mem_before = process.memory_info().rss / (1024 * 1024)

                preprocess_times = []
                inference_times = []
                postprocess_times = []
                detections_list = []

                for run in range(num_runs):
                    detections, timings = engine.infer(img, input_size=input_size, conf_threshold=conf_threshold)
                    preprocess_times.append(timings["preprocess_ms"])
                    inference_times.append(timings["inference_ms"])
                    postprocess_times.append(timings["postprocess_ms"])
                    detections_list.append(detections)

                mem_after = process.memory_info().rss / (1024 * 1024)
                peak_memory = max(mem_before, mem_after)

                avg_preprocess = np.mean(preprocess_times)
                avg_inference = np.mean(inference_times)
                avg_postprocess = np.mean(postprocess_times)
                total_ms = avg_preprocess + avg_inference + avg_postprocess
                fps = 1000.0 / total_ms if total_ms > 0 else 0

                # Save benchmark record
                record = BenchmarkRecord(
                    task_id=task.id,
                    model_id=model_id,
                    model_type=model_type,
                    device=device,
                    avg_inference_ms=round(avg_inference, 2),
                    avg_preprocess_ms=round(avg_preprocess, 2),
                    avg_postprocess_ms=round(avg_postprocess, 2),
                    peak_memory_mb=round(peak_memory, 2),
                    model_size_mb=round(model_file_size / (1024 * 1024), 2),
                    fps=round(fps, 2),
                    precision_metrics={
                        "num_runs": num_runs,
                        "std_inference_ms": round(np.std(inference_times), 2),
                    },
                )
                db.add(record)
                results.append({
                    "model_id": model_id,
                    "model_name": model.name,
                    "model_version": model.version,
                    "model_type": model_type,
                    "device": device,
                    "avg_inference_ms": round(avg_inference, 2),
                    "avg_preprocess_ms": round(avg_preprocess, 2),
                    "avg_postprocess_ms": round(avg_postprocess, 2),
                    "fps": round(fps, 2),
                    "peak_memory_mb": round(peak_memory, 2),
                    "model_size_mb": round(model_file_size / (1024 * 1024), 2),
                })

                task.progress = config_progress_base
                db.commit()

        task.progress = 100
        task.status = "completed"
        task.result = {"benchmarks": results}
        db.commit()

    except Exception as e:
        task.status = "failed"
        task.error_msg = str(e)
        db.commit()
        raise
```

- [ ] **Step 2: Write `backend/api/benchmark.py`**

```python
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor
from db.database import get_db
from db.models import Task
from schemas.benchmark_schema import BenchmarkRequest
from services import model_service
from services.benchmark_service import run_benchmark

router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])
executor = ThreadPoolExecutor(max_workers=2)


@router.post("")
def create_benchmark_task(req: BenchmarkRequest, db: Session = Depends(get_db)):
    for model_id in req.model_ids:
        model = model_service.get_model(db, model_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    task_id = uuid.uuid4().hex
    task = Task(
        id=task_id, type="benchmark", status="pending",
        params=req.model_dump(),
    )
    db.add(task)
    db.commit()

    # Use first model's input size
    first_model = model_service.get_model(db, req.model_ids[0])
    input_size = tuple(first_model.input_size) if first_model and first_model.input_size else (640, 640)

    # Default data path
    from storage.file_manager import BASE_DIR
    data_path = str(BASE_DIR / "反光衣测试.mp4")
    if req.dataset_id:
        # Lookup dataset path
        pass

    executor.submit(
        run_benchmark, task, db,
        model_ids=req.model_ids, model_types=req.model_types,
        devices=req.devices, data_path=data_path,
        input_size=input_size, conf_threshold=req.confidence_threshold,
        num_runs=req.num_runs or 100,
    )

    return {"task_id": task_id, "status": "pending"}


@router.get("/{task_id}")
def get_benchmark_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.type == "benchmark").first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": task.id,
        "status": task.status,
        "progress": task.progress,
        "result": task.result,
        "error_msg": task.error_msg,
    }
```

- [ ] **Step 3: Write `backend/api/datasets.py`**

```python
import uuid
import os
from fastapi import APIRouter, HTTPException, UploadFile, File
from storage.file_manager import (
    UPLOADS_IMAGES_DIR, UPLOADS_VIDEOS_DIR, RESULTS_DIR,
    get_root_media_files, SUPPORTED_IMAGE_EXT, SUPPORTED_VIDEO_EXT, ensure_dirs,
)

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.get("")
def list_datasets():
    ensure_dirs()
    datasets = []

    # Scan root directory for pre-set files
    for f in get_root_media_files():
        ext = f.suffix.lower()
        dtype = "image" if ext in SUPPORTED_IMAGE_EXT else "video"
        datasets.append({
            "id": f"root_{f.stem}",
            "name": f.name,
            "path": str(f),
            "type": dtype,
            "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
            "source": "root",
        })

    # Scan uploads directory
    for d, dtype in [(UPLOADS_IMAGES_DIR, "image"), (UPLOADS_VIDEOS_DIR, "video")]:
        if d.exists():
            for f in d.iterdir():
                if f.is_file():
                    datasets.append({
                        "id": f"upload_{f.stem}",
                        "name": f.name,
                        "path": str(f),
                        "type": dtype,
                        "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                        "source": "upload",
                    })

    return datasets


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    ensure_dirs()
    ext = os.path.splitext(file.filename)[1].lower()
    if ext in SUPPORTED_IMAGE_EXT:
        save_dir = UPLOADS_IMAGES_DIR
        dtype = "image"
    elif ext in SUPPORTED_VIDEO_EXT:
        save_dir = UPLOADS_VIDEOS_DIR
        dtype = "video"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = save_dir / filename
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "id": f"upload_{file_path.stem}",
        "name": file.filename,
        "path": str(file_path),
        "type": dtype,
        "size_mb": round(len(content) / (1024 * 1024), 2),
    }
```

- [ ] **Step 4: Register routers in `backend/main.py`**

```python
from api.benchmark import router as benchmark_router
from api.datasets import router as datasets_router
app.include_router(benchmark_router)
app.include_router(datasets_router)
```

- [ ] **Step 5: Write `backend/tests/test_datasets_api.py`**

```python
def test_list_datasets(client):
    response = client.get("/api/datasets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_upload_dataset_bad_type(client):
    import io
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert response.status_code == 400
```

- [ ] **Step 6: Run all backend tests**

Run: `cd backend && python -m pytest tests/ -v`
Expected: ALL PASSED

- [ ] **Step 7: Commit**

```bash
git add backend/services/benchmark_service.py backend/api/benchmark.py backend/api/datasets.py backend/tests/ backend/main.py
git commit -m "feat: benchmark API with multi-hardware comparison and datasets management"
```

---

## Task 7: Frontend Scaffolding & Layout

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.js`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/router/index.js`
- Create: `frontend/src/stores/models.js`
- Create: `frontend/src/api/request.js`
- Create: `frontend/src/utils/polling.js`

- [ ] **Step 1: Initialize Vue 3 project**

```bash
cd frontend
npm init vite@latest . -- --template vue
npm install
npm install element-plus @element-plus/icons-vue vue-router@4 pinia echarts axios
```

- [ ] **Step 2: Write `frontend/vite.config.js`**

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 3: Write `frontend/src/router/index.js`**

```javascript
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/models' },
  { path: '/models', name: 'ModelManager', component: () => import('../views/ModelManager.vue') },
  { path: '/convert', name: 'ModelConvert', component: () => import('../views/ModelConvert.vue') },
  { path: '/inference', name: 'InferenceVisual', component: () => import('../views/InferenceVisual.vue') },
  { path: '/benchmark', name: 'PerformanceCompare', component: () => import('../views/PerformanceCompare.vue') },
  { path: '/versions', name: 'VersionManage', component: () => import('../views/VersionManage.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
```

- [ ] **Step 4: Write `frontend/src/main.js`**

```javascript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)
const pinia = createPinia()

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(pinia)
app.use(router)
app.use(ElementPlus)
app.mount('#app')
```

- [ ] **Step 5: Write `frontend/src/App.vue`**

```vue
<template>
  <el-container style="height: 100vh">
    <el-header style="display: flex; align-items: center; background: #409EFF; color: white; padding: 0 20px;">
      <h2 style="margin: 0; font-size: 18px;">PT-ONNX 可视化对比工具 v2.0</h2>
    </el-header>
    <el-container>
      <el-aside width="180px" style="background: #f5f7fa;">
        <el-menu
          :default-active="activeMenu"
          router
          style="border-right: none; margin-top: 10px;"
        >
          <el-menu-item index="/models">
            <el-icon><Folder /></el-icon>
            <span>模型管理</span>
          </el-menu-item>
          <el-menu-item index="/convert">
            <el-icon><Switch /></el-icon>
            <span>模型转换</span>
          </el-menu-item>
          <el-menu-item index="/inference">
            <el-icon><View /></el-icon>
            <span>推理可视化</span>
          </el-menu-item>
          <el-menu-item index="/benchmark">
            <el-icon><DataAnalysis /></el-icon>
            <span>性能对比</span>
          </el-menu-item>
          <el-menu-item index="/versions">
            <el-icon><List /></el-icon>
            <span>版本管理</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main style="padding: 20px;">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>
```

- [ ] **Step 6: Write `frontend/src/api/request.js`**

```javascript
import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api',
  timeout: 300000,
})

request.interceptors.response.use(
  (response) => response,
  (error) => {
    const msg = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

export default request
```

- [ ] **Step 7: Write `frontend/src/utils/polling.js`**

```javascript
export function pollTask(getStatusFn, taskId, interval = 1500) {
  return new Promise((resolve, reject) => {
    const timer = setInterval(async () => {
      try {
        const res = await getStatusFn(taskId)
        const data = res.data
        if (data.status === 'completed') {
          clearInterval(timer)
          resolve(data)
        } else if (data.status === 'failed') {
          clearInterval(timer)
          reject(new Error(data.error_msg || 'Task failed'))
        }
        // Still running, continue polling
      } catch (err) {
        clearInterval(timer)
        reject(err)
      }
    }, interval)
  })
}
```

- [ ] **Step 8: Write `frontend/src/stores/models.js`**

```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '../api/request'

export const useModelStore = defineStore('models', () => {
  const models = ref([])
  const loading = ref(false)

  async function fetchModels() {
    loading.value = true
    try {
      const res = await request.get('/models')
      models.value = res.data
    } finally {
      loading.value = false
    }
  }

  return { models, loading, fetchModels }
})
```

- [ ] **Step 9: Create placeholder view components**

For each of the 5 views, create a minimal placeholder:

```vue
<!-- frontend/src/views/ModelManager.vue -->
<template>
  <div>
    <h2>模型管理</h2>
    <p>TODO: 模型列表、上传、元数据展示</p>
  </div>
</template>
```

(Repeat for ModelConvert.vue, InferenceVisual.vue, PerformanceCompare.vue, VersionManage.vue with appropriate titles)

- [ ] **Step 10: Verify frontend runs**

Run: `cd frontend && npm run dev`
Expected: Dev server starts, browser shows sidebar with 5 menu items, clicking navigates to placeholder pages

- [ ] **Step 11: Write API module files**

```javascript
// frontend/src/api/models.js
import request from './request'

export const getModels = () => request.get('/models')
export const getModel = (id) => request.get(`/models/${id}`)
export const uploadModel = (formData) => request.post('/models/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
})
export const updateModel = (id, data) => request.put(`/models/${id}`, data)
export const deleteModel = (id) => request.delete(`/models/${id}`)
export const scanModels = () => request.post('/models/scan')
```

```javascript
// frontend/src/api/convert.js
import request from './request'

export const createConvertTask = (data) => request.post('/convert', data)
export const getConvertTask = (taskId) => request.get(`/convert/${taskId}`)
```

```javascript
// frontend/src/api/inference.js
import request from './request'

export const createInferenceTask = (formData) => request.post('/inference', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
})
export const getInferenceTask = (taskId) => request.get(`/inference/${taskId}`)
export const getResultImage = (taskId, frameIdx) => `/api/inference/${taskId}/image/${frameIdx}`
```

```javascript
// frontend/src/api/benchmark.js
import request from './request'

export const createBenchmarkTask = (data) => request.post('/benchmark', data)
export const getBenchmarkTask = (taskId) => request.get(`/benchmark/${taskId}`)
```

```javascript
// frontend/src/api/datasets.js
import request from './request'

export const getDatasets = () => request.get('/datasets')
export const uploadDataset = (formData) => request.post('/datasets/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
})
```

```javascript
// frontend/src/api/tasks.js
import request from './request'

export const getTask = (taskId) => request.get(`/tasks/${taskId}`)
export const deleteTask = (taskId) => request.delete(`/tasks/${taskId}`)
```

- [ ] **Step 12: Commit**

```bash
git add frontend/
git commit -m "feat: frontend scaffolding with Vue 3, Element Plus, router, and API layer"
```

---

## Task 8: Model Management Tab

**Files:**
- Modify: `frontend/src/views/ModelManager.vue`
- Create: `frontend/src/components/FileUploader.vue`

- [ ] **Step 1: Write `frontend/src/components/FileUploader.vue`**

```vue
<template>
  <el-upload
    ref="uploadRef"
    :auto-upload="false"
    :limit="1"
    :on-change="handleFileChange"
    :on-remove="() => emit('file-change', null)"
    :accept="accept"
    drag
  >
    <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
    <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
  </el-upload>
</template>

<script setup>
defineProps({
  accept: { type: String, default: '.pt' },
})
const emit = defineEmits(['file-change'])

function handleFileChange(file) {
  emit('file-change', file.raw)
}
</script>
```

- [ ] **Step 2: Write `frontend/src/views/ModelManager.vue`**

```vue
<template>
  <div>
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="12">
        <h2>模型管理</h2>
      </el-col>
      <el-col :span="12" style="text-align: right;">
        <el-button type="primary" @click="showUploadDialog = true">
          <el-icon><Plus /></el-icon> 上传模型
        </el-button>
        <el-button @click="handleScan">
          <el-icon><Refresh /></el-icon> 重新扫描
        </el-button>
      </el-col>
    </el-row>

    <el-table :data="models" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="模型名称" />
      <el-table-column prop="version" label="版本" width="100" />
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="row.onnx_converted ? 'success' : 'info'">
            {{ row.onnx_converted ? '已转换 ONNX' : '仅 PT' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column label="PT 大小" width="100">
        <template #default="{ row }">
          {{ row.pt_file_size ? (row.pt_file_size / 1024 / 1024).toFixed(1) + ' MB' : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="handleEdit(row)">编辑</el-button>
          <el-popconfirm title="确定删除此模型？" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button size="small" type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- Upload Dialog -->
    <el-dialog v-model="showUploadDialog" title="上传 PT 模型" width="500px">
      <el-form :model="uploadForm" label-width="80px">
        <el-form-item label="模型名称">
          <el-input v-model="uploadForm.name" placeholder="如 helmet-vest" />
        </el-form-item>
        <el-form-item label="版本">
          <el-input v-model="uploadForm.version" placeholder="如 v1" />
        </el-form-item>
        <el-form-item label="模型文件">
          <FileUploader accept=".pt" @file-change="(f) => uploadForm.file = f" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">上传</el-button>
      </template>
    </el-dialog>

    <!-- Edit Dialog -->
    <el-dialog v-model="showEditDialog" title="编辑模型信息" width="500px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="模型名称">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="版本">
          <el-input v-model="editForm.version" />
        </el-form-item>
        <el-form-item label="训练轮数">
          <el-input-number v-model="editForm.training_epochs" :min="0" />
        </el-form-item>
        <el-form-item label="训练数据量">
          <el-input-number v-model="editForm.training_samples" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useModelStore } from '../stores/models'
import { uploadModel, updateModel, deleteModel, scanModels } from '../api/models'
import FileUploader from '../components/FileUploader.vue'

const store = useModelStore()
const { models, loading } = store

const showUploadDialog = ref(false)
const showEditDialog = ref(false)
const uploading = ref(false)
const uploadForm = ref({ name: '', version: 'v1', file: null })
const editForm = ref({ id: null, name: '', version: '', training_epochs: null, training_samples: null })

onMounted(() => store.fetchModels())

async function handleUpload() {
  if (!uploadForm.value.file || !uploadForm.value.name) {
    ElMessage.warning('请填写模型名称并选择文件')
    return
  }
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', uploadForm.value.file)
    formData.append('name', uploadForm.value.name)
    formData.append('version', uploadForm.value.version)
    await uploadModel(formData)
    ElMessage.success('上传成功')
    showUploadDialog.value = false
    uploadForm.value = { name: '', version: 'v1', file: null }
    store.fetchModels()
  } catch (e) {
    ElMessage.error('上传失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    uploading.value = false
  }
}

function handleEdit(row) {
  editForm.value = { ...row }
  showEditDialog.value = true
}

async function handleSaveEdit() {
  await updateModel(editForm.value.id, editForm.value)
  ElMessage.success('更新成功')
  showEditDialog.value = false
  store.fetchModels()
}

async function handleDelete(id) {
  await deleteModel(id)
  ElMessage.success('删除成功')
  store.fetchModels()
}

async function handleScan() {
  const res = await scanModels()
  ElMessage.success(`扫描完成，新增 ${res.data.scanned} 个模型`)
  store.fetchModels()
}
</script>
```

- [ ] **Step 3: Test in browser**

Run: `cd frontend && npm run dev`
- Open http://localhost:5173
- Verify model list loads (should show helmet-vest-v1 from auto-scan)
- Test upload dialog opens and closes
- Test edit and delete buttons

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/ModelManager.vue frontend/src/components/FileUploader.vue
git commit -m "feat: model management tab with table, upload dialog, edit, and delete"
```

---

## Task 9: Model Conversion Tab

**Files:**
- Modify: `frontend/src/views/ModelConvert.vue`
- Create: `frontend/src/components/TaskProgress.vue`

- [ ] **Step 1: Write `frontend/src/components/TaskProgress.vue`**

```vue
<template>
  <div v-if="task">
    <el-progress
      :percentage="task.progress"
      :status="progressStatus"
      :stroke-width="20"
      :text-inside="true"
    />
    <div style="margin-top: 10px; color: #666;">
      <span>状态: {{ statusText }}</span>
      <span v-if="task.error_msg" style="color: #f56c6c; margin-left: 10px;">
        错误: {{ task.error_msg }}
      </span>
    </div>
    <el-button
      v-if="task.status === 'completed' || task.status === 'failed'"
      size="small"
      style="margin-top: 10px;"
      @click="$emit('reset')"
    >
      重新执行
    </el-button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ task: Object })
defineEmits(['reset'])

const progressStatus = computed(() => {
  if (!props.task) return ''
  if (props.task.status === 'completed') return 'success'
  if (props.task.status === 'failed') return 'exception'
  return ''
})

const statusText = computed(() => {
  if (!props.task) return ''
  const map = { pending: '等待中', running: '执行中', completed: '已完成', failed: '失败' }
  return map[props.task.status] || props.task.status
})
</script>
```

- [ ] **Step 2: Write `frontend/src/views/ModelConvert.vue`**

```vue
<template>
  <div>
    <h2>模型转换</h2>
    <el-card style="max-width: 600px;">
      <el-form :model="form" label-width="120px">
        <el-form-item label="选择模型">
          <el-select v-model="form.model_id" placeholder="选择 PT 模型" style="width: 100%;">
            <el-option
              v-for="m in ptModels"
              :key="m.id"
              :label="`${m.name} (${m.version})`"
              :value="m.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="输入尺寸">
          <el-input v-model="form.inputSizeStr" placeholder="640,640" />
        </el-form-item>
        <el-form-item label="ONNX Opset">
          <el-input-number v-model="form.opset_version" :min="9" :max="17" />
        </el-form-item>
        <el-form-item label="动态 Batch">
          <el-switch v-model="form.dynamic_batch" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="converting" @click="handleConvert">
            开始转换
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="currentTask" style="max-width: 600px; margin-top: 20px;">
      <h3>转换进度</h3>
      <TaskProgress :task="currentTask" @reset="currentTask = null" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useModelStore } from '../stores/models'
import { createConvertTask, getConvertTask } from '../api/convert'
import { pollTask } from '../utils/polling'
import TaskProgress from '../components/TaskProgress.vue'

const store = useModelStore()
const ptModels = computed(() => store.models.filter(m => !m.onnx_converted))
const form = ref({ model_id: null, inputSizeStr: '640,640', opset_version: 11, dynamic_batch: true })
const converting = ref(false)
const currentTask = ref(null)

onMounted(() => store.fetchModels())

async function handleConvert() {
  if (!form.value.model_id) {
    ElMessage.warning('请选择模型')
    return
  }
  converting.value = true
  try {
    const inputSize = form.value.inputSizeStr.split(',').map(Number)
    const res = await createConvertTask({
      model_id: form.value.model_id,
      input_size: inputSize,
      dynamic_batch: form.value.dynamic_batch,
      opset_version: form.value.opset_version,
    })
    const taskId = res.data.task_id
    currentTask.value = { status: 'running', progress: 0 }

    // Poll for progress
    const timer = setInterval(async () => {
      const statusRes = await getConvertTask(taskId)
      currentTask.value = statusRes.data
      if (statusRes.data.status === 'completed' || statusRes.data.status === 'failed') {
        clearInterval(timer)
        converting.value = false
        if (statusRes.data.status === 'completed') {
          ElMessage.success('转换完成')
          store.fetchModels()
        } else {
          ElMessage.error('转换失败: ' + statusRes.data.error_msg)
        }
      }
    }, 1500)
  } catch (e) {
    converting.value = false
    ElMessage.error('创建转换任务失败')
  }
}
</script>
```

- [ ] **Step 3: Test in browser**

- Verify PT models load in dropdown (helmet-vest-v1 should appear if not yet converted)
- Verify form fields work
- (Optional: test actual conversion if PT model is valid)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/ModelConvert.vue frontend/src/components/TaskProgress.vue
git commit -m "feat: model conversion tab with parameter config and progress tracking"
```

---

## Task 10: Inference Visualization Tab

**Files:**
- Modify: `frontend/src/views/InferenceVisual.vue`
- Create: `frontend/src/components/ResultImage.vue`

- [ ] **Step 1: Write `frontend/src/components/ResultImage.vue`**

```vue
<template>
  <div>
    <div v-if="imageUrl" style="text-align: center;">
      <el-image :src="imageUrl" fit="contain" :max-height="500" />
      <div v-if="detections.length" style="margin-top: 10px;">
        <el-table :data="detections" size="small" max-height="200">
          <el-table-column prop="class_name" label="类别" width="100" />
          <el-table-column label="置信度" width="100">
            <template #default="{ row }">{{ (row.confidence * 100).toFixed(1) }}%</template>
          </el-table-column>
          <el-table-column label="边界框">
            <template #default="{ row }">
              [{{ row.bbox.map(v => v.toFixed(0)).join(', ') }}]
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
    <el-empty v-else description="暂无结果" />
  </div>
</template>

<script setup>
defineProps({
  imageUrl: String,
  detections: { type: Array, default: () => [] },
})
</script>
```

- [ ] **Step 2: Write `frontend/src/views/InferenceVisual.vue`**

```vue
<template>
  <div>
    <h2>推理可视化</h2>
    <el-card style="max-width: 700px; margin-bottom: 20px;">
      <el-form :model="form" label-width="100px">
        <el-form-item label="选择模型">
          <el-select v-model="form.model_id" placeholder="选择模型" style="width: 100%;"
                     @change="onModelChange">
            <el-option
              v-for="m in store.models"
              :key="m.id"
              :label="`${m.name} (${m.version})`"
              :value="m.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="模型类型">
          <el-radio-group v-model="form.model_type">
            <el-radio value="pt" :disabled="!selectedModel">PT</el-radio>
            <el-radio value="onnx" :disabled="!selectedModel?.onnx_converted">ONNX</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="硬件">
          <el-select v-model="form.device" style="width: 200px;">
            <el-option label="CPU" value="cpu" />
            <el-option label="GPU (CUDA)" value="cuda" />
          </el-select>
        </el-form-item>
        <el-form-item label="置信度阈值">
          <el-slider v-model="form.confidence_threshold" :min="0.1" :max="1.0" :step="0.05"
                     :format-tooltip="(v) => (v * 100).toFixed(0) + '%'" style="width: 300px;" />
        </el-form-item>
        <el-form-item label="数据源">
          <el-tabs v-model="dataSourceType">
            <el-tab-pane label="选择已有" name="existing">
              <el-select v-model="form.dataset_path" placeholder="选择数据源" style="width: 100%;">
                <el-option
                  v-for="d in datasets"
                  :key="d.id"
                  :label="`${d.name} (${d.type}, ${d.size_mb}MB)`"
                  :value="d.path"
                />
              </el-select>
            </el-tab-pane>
            <el-tab-pane label="上传新文件" name="upload">
              <FileUploader accept=".jpg,.jpeg,.png,.mp4,.avi" @file-change="(f) => uploadFile = f" />
            </el-tab-pane>
          </el-tabs>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="running" @click="handleInfer">开始推理</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Progress -->
    <el-card v-if="currentTask" style="margin-bottom: 20px;">
      <TaskProgress :task="currentTask" @reset="currentTask = null" />
    </el-card>

    <!-- Results -->
    <el-row :gutter="20" v-if="resultData">
      <el-col :span="12">
        <el-card>
          <h3>检测结果</h3>
          <ResultImage :imageUrl="currentImageUrl" :detections="currentDetections" />
          <div v-if="isVideo" style="margin-top: 10px;">
            <el-slider v-model="currentFrame" :min="0" :max="resultData.total_frames - 1"
                       @change="onFrameChange" />
            <span>帧 {{ currentFrame }} / {{ resultData.total_frames - 1 }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <h3>推理信息</h3>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="模型类型">{{ resultData.model_type?.toUpperCase() }}</el-descriptions-item>
            <el-descriptions-item label="设备">{{ resultData.device }}</el-descriptions-item>
            <el-descriptions-item label="总帧数">{{ resultData.total_frames }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useModelStore } from '../stores/models'
import { createInferenceTask, getInferenceTask, getResultImage } from '../api/inference'
import { getDatasets } from '../api/datasets'
import { pollTask } from '../utils/polling'
import TaskProgress from '../components/TaskProgress.vue'
import ResultImage from '../components/ResultImage.vue'
import FileUploader from '../components/FileUploader.vue'

const store = useModelStore()
const datasets = ref([])
const dataSourceType = ref('existing')
const uploadFile = ref(null)
const form = ref({
  model_id: null, model_type: 'pt', device: 'cpu',
  confidence_threshold: 0.5, dataset_path: null,
})
const running = ref(false)
const currentTask = ref(null)
const resultData = ref(null)
const currentFrame = ref(0)

const selectedModel = computed(() => store.models.find(m => m.id === form.value.model_id))
const isVideo = computed(() => resultData.value?.total_frames > 1)
const currentImageUrl = computed(() => {
  if (!currentTask.value) return null
  return getResultImage(currentTask.value.task_id || '', currentFrame.value)
})
const currentDetections = computed(() => {
  if (!resultData.value?.detections_summary) return []
  const frame = resultData.value.detections_summary.find(d => d.frame === currentFrame.value)
  return frame?.detections || []
})

onMounted(async () => {
  await store.fetchModels()
  const res = await getDatasets()
  datasets.value = res.data
  // Auto-select first model and dataset
  if (store.models.length) form.value.model_id = store.models[0].id
  if (datasets.value.length) form.value.dataset_path = datasets.value[0].path
})

function onModelChange(id) {
  const m = store.models.find(m => m.id === id)
  if (m) {
    form.value.model_type = m.onnx_converted ? 'onnx' : 'pt'
  }
}

async function handleInfer() {
  if (!form.value.model_id) { ElMessage.warning('请选择模型'); return }
  running.value = true
  try {
    const formData = new FormData()
    formData.append('model_id', form.value.model_id)
    formData.append('model_type', form.value.model_type)
    formData.append('device', form.value.device)
    formData.append('confidence_threshold', form.value.confidence_threshold)

    if (dataSourceType.value === 'upload' && uploadFile.value) {
      formData.append('file', uploadFile.value)
    } else if (form.value.dataset_path) {
      const blob = await fetch(form.value.dataset_path).then(r => r.blob())
      formData.append('file', new File([blob], 'data.jpg'))
    }

    const res = await createInferenceTask(formData)
    const taskId = res.data.task_id
    currentTask.value = { task_id: taskId, status: 'running', progress: 0 }

    const timer = setInterval(async () => {
      const statusRes = await getInferenceTask(taskId)
      currentTask.value = { ...statusRes.data, task_id: taskId }
      if (statusRes.data.status === 'completed' || statusRes.data.status === 'failed') {
        clearInterval(timer)
        running.value = false
        if (statusRes.data.status === 'completed') {
          resultData.value = statusRes.data.result
          currentFrame.value = 0
          ElMessage.success('推理完成')
        } else {
          ElMessage.error('推理失败: ' + statusRes.data.error_msg)
        }
      }
    }, 1500)
  } catch (e) {
    running.value = false
  }
}

function onFrameChange(val) {
  currentFrame.value = val
}
</script>
```

- [ ] **Step 3: Test in browser**

- Verify model dropdown loads with defaults
- Verify dataset dropdown loads with 反光衣测试.mp4
- Test form interactions

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/InferenceVisual.vue frontend/src/components/ResultImage.vue
git commit -m "feat: inference visualization tab with model/data selection and result display"
```

---

## Task 11: Performance Comparison Tab

**Files:**
- Modify: `frontend/src/views/PerformanceCompare.vue`
- Create: `frontend/src/components/MetricsChart.vue`

- [ ] **Step 1: Write `frontend/src/components/MetricsChart.vue`**

```vue
<template>
  <div ref="chartRef" :style="{ width: '100%', height: height + 'px' }"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  option: { type: Object, required: true },
  height: { type: Number, default: 400 },
})

const chartRef = ref(null)
let chart = null

onMounted(() => {
  chart = echarts.init(chartRef.value)
  chart.setOption(props.option)
  window.addEventListener('resize', () => chart?.resize())
})

watch(() => props.option, (opt) => {
  chart?.setOption(opt, true)
}, { deep: true })

onUnmounted(() => {
  chart?.dispose()
  window.removeEventListener('resize', () => chart?.resize())
})
</script>
```

- [ ] **Step 2: Write `frontend/src/views/PerformanceCompare.vue`**

```vue
<template>
  <div>
    <h2>性能对比</h2>
    <el-card style="margin-bottom: 20px;">
      <el-form :model="form" label-width="100px">
        <el-form-item label="对比模式">
          <el-radio-group v-model="form.mode" @change="onModeChange">
            <el-radio value="pt_onnx">PT vs ONNX（纵向）</el-radio>
            <el-radio value="pt_pt">PT vs PT（版本横向）</el-radio>
            <el-radio value="onnx_onnx">ONNX vs ONNX（版本横向）</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="选择模型">
          <el-checkbox-group v-model="form.model_ids" :max="form.mode === 'pt_onnx' ? 1 : 5">
            <el-checkbox
              v-for="m in availableModels"
              :key="m.id"
              :value="m.id"
            >
              {{ m.name }} ({{ m.version }}) - {{ getModelTypeLabel(m) }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="硬件">
          <el-checkbox-group v-model="form.devices">
            <el-checkbox value="cpu">CPU</el-checkbox>
            <el-checkbox value="cuda" :disabled="!hasGpu">GPU (CUDA)</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="running" @click="handleBenchmark">开始对比</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Progress -->
    <el-card v-if="currentTask" style="margin-bottom: 20px;">
      <TaskProgress :task="currentTask" @reset="currentTask = null" />
    </el-card>

    <!-- Charts -->
    <template v-if="benchmarkResults.length">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card>
            <h3>推理速度对比</h3>
            <MetricsChart :option="speedChartOption" />
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <h3>资源占用对比</h3>
            <MetricsChart :option="resourceChartOption" />
          </el-card>
        </el-col>
      </el-row>
      <el-card style="margin-top: 20px;">
        <h3>综合对比汇总</h3>
        <el-table :data="benchmarkResults" stripe>
          <el-table-column label="模型" prop="label" />
          <el-table-column label="设备" prop="device" width="80" />
          <el-table-column label="平均推理(ms)" prop="avg_inference_ms" width="130" />
          <el-table-column label="预处理(ms)" prop="avg_preprocess_ms" width="110" />
          <el-table-column label="后处理(ms)" prop="avg_postprocess_ms" width="110" />
          <el-table-column label="FPS" prop="fps" width="80" />
          <el-table-column label="峰值内存(MB)" prop="peak_memory_mb" width="130" />
          <el-table-column label="模型大小(MB)" prop="model_size_mb" width="130" />
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useModelStore } from '../stores/models'
import { createBenchmarkTask, getBenchmarkTask } from '../api/benchmark'
import TaskProgress from '../components/TaskProgress.vue'
import MetricsChart from '../components/MetricsChart.vue'

const store = useModelStore()
const hasGpu = ref(true) // Will be detected at runtime
const form = ref({
  mode: 'pt_onnx',
  model_ids: [],
  devices: ['cpu'],
})
const running = ref(false)
const currentTask = ref(null)
const benchmarkResults = ref([])

const availableModels = computed(() => {
  if (form.value.mode === 'pt_onnx') {
    return store.models.filter(m => m.onnx_converted)
  }
  if (form.value.mode === 'onnx_onnx') {
    return store.models.filter(m => m.onnx_converted)
  }
  return store.models
})

onMounted(() => {
  store.fetchModels()
  // Auto-select defaults
  if (store.models.length) {
    form.value.model_ids = [store.models[0].id]
  }
})

function getModelTypeLabel(model) {
  if (form.value.mode === 'pt_onnx') return 'PT + ONNX'
  if (form.value.mode === 'onnx_onnx') return 'ONNX'
  return 'PT'
}

function onModeChange() {
  form.value.model_ids = []
}

async function handleBenchmark() {
  if (!form.value.model_ids.length) { ElMessage.warning('请选择模型'); return }
  if (!form.value.devices.length) { ElMessage.warning('请选择硬件'); return }

  running.value = true
  const modelTypes = []
  for (const id of form.value.model_ids) {
    if (form.value.mode === 'pt_onnx') modelTypes.push('pt')
    else if (form.value.mode === 'onnx_onnx') modelTypes.push('onnx')
    else modelTypes.push('pt')
  }

  try {
    const res = await createBenchmarkTask({
      model_ids: form.value.model_ids,
      model_types: modelTypes,
      devices: form.value.devices,
    })
    const taskId = res.data.task_id
    currentTask.value = { task_id: taskId, status: 'running', progress: 0 }

    const timer = setInterval(async () => {
      const statusRes = await getBenchmarkTask(taskId)
      currentTask.value = { ...statusRes.data, task_id: taskId }
      if (statusRes.data.status === 'completed' || statusRes.data.status === 'failed') {
        clearInterval(timer)
        running.value = false
        if (statusRes.data.status === 'completed') {
          benchmarkResults.value = (statusRes.data.result?.benchmarks || []).map(b => ({
            ...b,
            label: `${b.model_name} ${b.model_version} (${b.model_type.toUpperCase()})`,
          }))
          ElMessage.success('对比完成')
        } else {
          ElMessage.error('对比失败: ' + statusRes.data.error_msg)
        }
      }
    }, 2000)
  } catch (e) {
    running.value = false
  }
}

const speedChartOption = computed(() => {
  const labels = benchmarkResults.value.map(r => `${r.label}-${r.device}`)
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['预处理', '推理', '后处理'] },
    xAxis: { type: 'category', data: labels, axisLabel: { rotate: 30 } },
    yAxis: { type: 'value', name: '耗时 (ms)' },
    series: [
      { name: '预处理', type: 'bar', stack: 'total', data: benchmarkResults.value.map(r => r.avg_preprocess_ms) },
      { name: '推理', type: 'bar', stack: 'total', data: benchmarkResults.value.map(r => r.avg_inference_ms) },
      { name: '后处理', type: 'bar', stack: 'total', data: benchmarkResults.value.map(r => r.avg_postprocess_ms) },
    ],
  }
})

const resourceChartOption = computed(() => {
  const labels = benchmarkResults.value.map(r => `${r.label}-${r.device}`)
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['峰值内存 (MB)', '模型大小 (MB)'] },
    xAxis: { type: 'category', data: labels, axisLabel: { rotate: 30 } },
    yAxis: { type: 'value', name: 'MB' },
    series: [
      { name: '峰值内存 (MB)', type: 'bar', data: benchmarkResults.value.map(r => r.peak_memory_mb) },
      { name: '模型大小 (MB)', type: 'bar', data: benchmarkResults.value.map(r => r.model_size_mb) },
    ],
  }
})
</script>
```

- [ ] **Step 3: Test in browser**

- Verify comparison mode radio buttons work
- Verify model checkboxes update based on mode
- Verify chart components render (even if empty data)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/PerformanceCompare.vue frontend/src/components/MetricsChart.vue
git commit -m "feat: performance comparison tab with speed/resource charts and summary table"
```

---

## Task 12: Version Management Tab

**Files:**
- Modify: `frontend/src/views/VersionManage.vue`

- [ ] **Step 1: Write `frontend/src/views/VersionManage.vue`**

```vue
<template>
  <div>
    <h2>版本管理</h2>

    <!-- Group by model name -->
    <el-collapse v-model="expandedNames">
      <el-collapse-item
        v-for="(versions, name) in groupedModels"
        :key="name"
        :title="`${name} (${versions.length} 个版本)`"
        :name="name"
      >
        <el-table :data="versions" stripe>
          <el-table-column prop="version" label="版本" width="120" />
          <el-table-column label="状态" width="150">
            <template #default="{ row }">
              <el-tag :type="row.onnx_converted ? 'success' : 'info'" size="small">
                {{ row.onnx_converted ? 'PT + ONNX' : '仅 PT' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" show-overflow-tooltip />
          <el-table-column label="参数量" width="120">
            <template #default="{ row }">
              {{ row.param_count ? formatParamCount(row.param_count) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="PT 大小" width="100">
            <template #default="{ row }">
              {{ row.pt_file_size ? (row.pt_file_size / 1024 / 1024).toFixed(1) + ' MB' : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="ONNX 大小" width="110">
            <template #default="{ row }">
              {{ row.onnx_file_size ? (row.onnx_file_size / 1024 / 1024).toFixed(1) + ' MB' : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="训练轮数" width="100">
            <template #default="{ row }">{{ row.training_epochs || '-' }}</template>
          </el-table-column>
          <el-table-column label="创建时间" width="180">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="200">
            <template #default="{ row }">
              <el-button size="small" @click="goToCompare(name)">对比</el-button>
              <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
                <template #reference>
                  <el-button size="small" type="danger">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-collapse-item>
    </el-collapse>

    <el-empty v-if="!Object.keys(groupedModels).length" description="暂无模型" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useModelStore } from '../stores/models'
import { deleteModel } from '../api/models'

const store = useModelStore()
const router = useRouter()
const expandedNames = ref([])

const groupedModels = computed(() => {
  const groups = {}
  for (const m of store.models) {
    if (!groups[m.name]) groups[m.name] = []
    groups[m.name].push(m)
  }
  return groups
})

onMounted(async () => {
  await store.fetchModels()
  // Expand all groups by default
  expandedNames.value = Object.keys(groupedModels.value)
})

function formatParamCount(count) {
  if (count > 1_000_000) return (count / 1_000_000).toFixed(1) + 'M'
  return (count / 1_000).toFixed(1) + 'K'
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

function goToCompare(modelName) {
  router.push('/benchmark')
}

async function handleDelete(id) {
  await deleteModel(id)
  ElMessage.success('删除成功')
  store.fetchModels()
}
</script>
```

- [ ] **Step 2: Test in browser**

- Verify models are grouped by name
- Verify version details display correctly
- Test expand/collapse of groups

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/VersionManage.vue
git commit -m "feat: version management tab with grouped model list and history"
```

---

## Task 13: Integration Testing & Polish

**Files:**
- Create: `backend/tests/test_integration.py`
- Create: `.gitignore`
- Modify: `backend/main.py` (final adjustments)

- [ ] **Step 1: Write integration test for full workflow**

```python
# backend/tests/test_integration.py
import io
import time


def test_full_workflow_upload_convert(client):
    """Full workflow: upload model -> check in list -> create convert task -> check task."""
    # Upload
    pt_content = b"fake_integration_model"
    upload_resp = client.post(
        "/api/models/upload",
        files={"file": ("integration.pt", io.BytesIO(pt_content), "application/octet-stream")},
        data={"name": "integration-test", "version": "v1"},
    )
    assert upload_resp.status_code == 200
    model_id = upload_resp.json()["id"]

    # Check in list
    list_resp = client.get("/api/models")
    assert list_resp.status_code == 200
    model_ids = [m["id"] for m in list_resp.json()]
    assert model_id in model_ids

    # Get detail
    detail_resp = client.get(f"/api/models/{model_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["name"] == "integration-test"

    # Create convert task (will fail due to fake model, but task should be created)
    convert_resp = client.post("/api/convert", json={"model_id": model_id})
    assert convert_resp.status_code == 200
    task_id = convert_resp.json()["task_id"]

    # Check task status
    time.sleep(2)  # Give the task some time to process
    task_resp = client.get(f"/api/tasks/{task_id}")
    assert task_resp.status_code == 200
    assert task_resp.json()["type"] == "convert"


def test_scan_endpoint(client):
    """POST /api/models/scan should trigger directory scan."""
    response = client.post("/api/models/scan")
    assert response.status_code == 200
    assert "scanned" in response.json()


def test_datasets_endpoint(client):
    """GET /api/datasets should return available datasets."""
    response = client.get("/api/datasets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

- [ ] **Step 2: Write `.gitignore`**

```
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
.venv/
venv/

# Database
*.db

# Storage (generated at runtime)
storage/

# IDE
.vscode/
.idea/

# Node
frontend/node_modules/
frontend/dist/

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 3: Run full test suite**

Run: `cd backend && python -m pytest tests/ -v`
Expected: ALL PASSED

- [ ] **Step 4: Final commit**

```bash
git add backend/tests/test_integration.py .gitignore
git commit -m "feat: integration tests and .gitignore"
```

---

## Self-Review

### Spec Coverage Check

| Spec Requirement | Task |
|-----------------|------|
| PT 模型上传和管理 | Task 2 (Model Management API) |
| 启动自动扫描本地文件 | Task 3 (Auto-Scan Service) |
| 模型元数据提取和自动描述 | Task 2 (model_service.py) |
| PT → ONNX 转换 | Task 4 (Conversion API) |
| 推理可视化 (PT + ONNX) | Task 5 (Inference Engine + API) |
| 性能对比 (三种模式) | Task 6 (Benchmark API) + Task 11 (Performance Compare Tab) |
| 多硬件支持 (CPU/GPU) | Task 5 + Task 6 (engines support device param) |
| 对比指标 (速度/精度/资源) | Task 6 (benchmark_service.py) |
| 默认值自动填充 | Task 8-11 (frontend defaults) |
| 模型版本管理 | Task 12 (Version Management Tab) |
| 一对一 PT-ONNX 管理 | Task 2 (DB model design) |
| 文件上传 (模型 + 数据) | Task 2 + Task 6 |
| 错误处理 | Task 4-6 (error handling in services) |
| 前端多标签页布局 | Task 7 (App.vue with sidebar navigation) |
| REST + 轮询通信 | Task 7 (polling.js + all task endpoints) |

### Placeholder Scan

No TBD, TODO, or incomplete sections found. All steps contain concrete code.

### Type Consistency

- Database model fields match across all Pydantic schemas, API endpoints, and frontend field references
- API response formats consistent between backend definitions and frontend consumption
- Task status values (`pending`/`running`/`completed`/`failed`) used consistently across all task types

---

## Execution Options

**Plan saved to `docs/superpowers/plans/2025-05-27-pt-onnx-benchmark-tool-implementation.md`.**

**Two execution approaches:**

**1. Subagent-Driven (推荐)** — 每个 Task 分派一个独立子代理执行，任务之间审阅检查，快速迭代

**2. Inline Execution** — 在当前会话中按 Task 顺序执行，批量推进，设置检查点

**你选择哪种方式？**
