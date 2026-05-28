import uuid
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor
from db.database import get_db
from db.models import Task
from services import model_service
from services.inference_service import run_inference
from storage.file_manager import UPLOADS_IMAGES_DIR, UPLOADS_VIDEOS_DIR, RESULTS_DIR, ensure_dirs

router = APIRouter(prefix="/api/inference", tags=["inference"])
executor = ThreadPoolExecutor(max_workers=2)


@router.post("")
async def create_inference_task(
    model_id: int = Form(...),
    model_type: str = Form(...),
    device: str = Form("cpu"),
    confidence_threshold: float = Form(0.5),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    model = model_service.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if model_type == "onnx" and not model.onnx_converted:
        raise HTTPException(status_code=400, detail="Model not yet converted to ONNX")

    if not file:
        raise HTTPException(status_code=400, detail="No data source provided")

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

    task_id = uuid.uuid4().hex
    task = Task(
        id=task_id, type="inference", status="pending",
        params={"model_id": model_id, "model_type": model_type, "device": device,
                "confidence_threshold": confidence_threshold, "data_path": str(file_path)},
    )
    db.add(task)
    db.commit()

    input_size = tuple(model.input_size) if model.input_size else (640, 640)
    executor.submit(
        run_inference,
        model_id=model_id, task_id=task_id,
        model_type=model_type, device=device,
        data_path=str(file_path), input_size=input_size,
        conf_threshold=confidence_threshold,
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
    from fastapi.responses import FileResponse
    img_path = RESULTS_DIR / task_id / "annotated" / f"frame_{frame_idx:06d}.jpg"
    if not img_path.exists():
        img_path = RESULTS_DIR / task_id / "annotated" / "result.jpg"
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Result image not found")
    return FileResponse(str(img_path))
