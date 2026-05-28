import torch
from pathlib import Path
from db.database import SessionLocal
from db.models import Model as ModelDB, Task
from storage.file_manager import MODELS_ONNX_DIR


def convert_pt_to_onnx(model_id: int, task_id: str,
                       input_size=(640, 640), opset_version=11, dynamic_batch=True):
    """Convert a PT model to ONNX format. Runs in background thread with own DB session."""
    db = SessionLocal()
    try:
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        task = db.query(Task).filter(Task.id == task_id).first()

        task.status = "running"
        task.progress = 10
        db.commit()

        checkpoint = torch.load(model.pt_file_path, map_location="cpu", weights_only=False)
        task.progress = 30
        db.commit()

        if isinstance(checkpoint, dict) and "model" in checkpoint:
            pt_model = checkpoint["model"]
        elif hasattr(checkpoint, "model"):
            pt_model = checkpoint.model
        else:
            pt_model = checkpoint

        pt_model.eval()
        task.progress = 50
        db.commit()

        dummy_input = torch.randn(1, 3, input_size[0], input_size[1])

        pt_path = Path(model.pt_file_path)
        onnx_filename = pt_path.stem + ".onnx"
        onnx_path = MODELS_ONNX_DIR / onnx_filename
        onnx_path.parent.mkdir(parents=True, exist_ok=True)

        task.progress = 60
        db.commit()

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

        model.onnx_file_path = str(onnx_path)
        model.onnx_converted = True
        model.onnx_file_size = onnx_path.stat().st_size

        task.progress = 100
        task.status = "completed"
        task.result = {"onnx_path": str(onnx_path), "file_size": model.onnx_file_size}
        db.commit()

    except Exception as e:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = "failed"
            task.error_msg = str(e)
            db.commit()
    finally:
        db.close()
