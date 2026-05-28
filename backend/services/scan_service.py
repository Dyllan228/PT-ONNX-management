from pathlib import Path
from sqlalchemy.orm import Session
from db.models import Model as ModelDB
from services.model_service import extract_model_metadata
from storage.file_manager import BASE_DIR, MODELS_PT_DIR, MODELS_ONNX_DIR, ensure_dirs

SUPPORTED_PT_EXT = {".pt"}


def scan_and_register(db: Session) -> int:
    """Scan directories and register found models. Returns count of newly registered."""
    ensure_dirs()
    count = 0

    scan_dirs = [BASE_DIR, MODELS_PT_DIR]
    registered_paths = {m.pt_file_path for m in db.query(ModelDB).all()}

    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for f in scan_dir.iterdir():
            if not f.is_file() or f.suffix.lower() not in SUPPORTED_PT_EXT:
                continue
            abs_path = str(f.resolve())
            if abs_path in registered_paths:
                continue

            stem = f.stem
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

    for model in db.query(ModelDB).filter(ModelDB.onnx_converted == False).all():
        pt_path = Path(model.pt_file_path)
        onnx_path = MODELS_ONNX_DIR / pt_path.with_suffix(".onnx").name
        if onnx_path.exists():
            model.onnx_file_path = str(onnx_path)
            model.onnx_converted = True
            model.onnx_file_size = onnx_path.stat().st_size

    db.commit()
    return count
