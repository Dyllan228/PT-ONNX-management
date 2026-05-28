import uuid
import os
from typing import List
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
