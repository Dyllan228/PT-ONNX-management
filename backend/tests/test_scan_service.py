import uuid
from unittest.mock import patch
from db.database import SessionLocal
from services.scan_service import scan_and_register
from db.models import Model as ModelDB


def test_scan_registers_root_pt_files(tmp_path):
    """scan_and_register should find .pt files in the root directory."""
    unique_name = f"scan-test-{uuid.uuid4().hex[:8]}"
    fake_pt = tmp_path / f"{unique_name}.pt"
    fake_pt.write_bytes(b"fake_pt_content")

    storage_pt = tmp_path / "storage" / "models" / "pt"
    storage_pt.mkdir(parents=True, exist_ok=True)

    with patch("services.scan_service.BASE_DIR", tmp_path), \
         patch("services.scan_service.MODELS_PT_DIR", storage_pt), \
         patch("services.scan_service.MODELS_ONNX_DIR", tmp_path / "storage" / "models" / "onnx"):
        db = SessionLocal()
        try:
            count = scan_and_register(db)
            assert count >= 1
            models = db.query(ModelDB).all()
            assert any(m.name == unique_name for m in models)
        finally:
            db.close()


def test_scan_skips_duplicates(tmp_path):
    """Running scan twice should not create duplicates."""
    unique_name = f"dup-model-{uuid.uuid4().hex[:8]}"
    fake_pt = tmp_path / f"{unique_name}.pt"
    fake_pt.write_bytes(b"fake_pt_content")

    storage_pt = tmp_path / "storage" / "models" / "pt"
    storage_pt.mkdir(parents=True, exist_ok=True)

    with patch("services.scan_service.BASE_DIR", tmp_path), \
         patch("services.scan_service.MODELS_PT_DIR", storage_pt), \
         patch("services.scan_service.MODELS_ONNX_DIR", tmp_path / "storage" / "models" / "onnx"):
        db = SessionLocal()
        try:
            scan_and_register(db)
            count1 = db.query(ModelDB).count()
            scan_and_register(db)
            count2 = db.query(ModelDB).count()
            assert count1 == count2
        finally:
            db.close()
