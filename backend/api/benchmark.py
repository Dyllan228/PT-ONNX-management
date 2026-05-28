import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor
from db.database import get_db
from db.models import Task
from schemas.benchmark_schema import BenchmarkRequest
from services import model_service
from services.benchmark_service import run_benchmark
from storage.file_manager import BASE_DIR

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

    first_model = model_service.get_model(db, req.model_ids[0])
    input_size = tuple(first_model.input_size) if first_model and first_model.input_size else (640, 640)

    data_path = str(BASE_DIR / "反光衣测试.mp4")
    if req.dataset_id:
        pass

    executor.submit(
        run_benchmark,
        task_id=task_id,
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
