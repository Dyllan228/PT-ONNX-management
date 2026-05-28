import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor
from db.database import get_db
from db.models import Task
from schemas.convert_schema import ConvertRequest
from services import model_service
from services.convert_service import convert_pt_to_onnx

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
    task = Task(
        id=task_id, type="convert", status="pending",
        params={"model_id": req.model_id, "input_size": req.input_size,
                "opset_version": req.opset_version, "dynamic_batch": req.dynamic_batch},
    )
    db.add(task)
    db.commit()

    executor.submit(
        convert_pt_to_onnx,
        model_id=req.model_id, task_id=task_id,
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
