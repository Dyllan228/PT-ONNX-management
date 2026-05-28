import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.model_schema import ModelResponse, ModelUpdate
from services import model_service
from storage.file_manager import MODELS_PT_DIR, ensure_dirs

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=List[ModelResponse])
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
