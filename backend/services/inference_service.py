import cv2
from pathlib import Path
from db.database import SessionLocal
from db.models import Model as ModelDB, Task
from engines.pt_engine import PTEngine
from engines.onnx_engine import ONNXEngine
from storage.file_manager import RESULTS_DIR


def draw_detections(img, detections):
    for det in detections:
        x1, y1, x2, y2 = [int(v) for v in det["bbox"]]
        label = f"{det['class_name']} {det['confidence']:.2f}"
        color = (0, 255, 0)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return img


def run_inference(model_id: int, task_id: str, model_type: str, device: str,
                  data_path: str, input_size=(640, 640), conf_threshold=0.5):
    """Run inference on image or video. Runs in background thread with own DB session."""
    db = SessionLocal()
    try:
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        task = db.query(Task).filter(Task.id == task_id).first()

        task.status = "running"
        task.progress = 5
        db.commit()

        if model_type == "pt":
            engine = PTEngine(model.pt_file_path, device=device)
        else:
            engine = ONNXEngine(model.onnx_file_path, device=device)
            if model.class_names:
                engine.set_names({i: n for i, n in enumerate(model.class_names)})

        task.progress = 15
        db.commit()

        result_dir = RESULTS_DIR / task_id
        annotated_dir = result_dir / "annotated"
        annotated_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(data_path).suffix.lower()
        all_detections = []

        if ext in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
            img = cv2.imread(data_path)
            if img is None:
                raise ValueError(f"Cannot read image: {data_path}")
            detections, timings = engine.infer(img, input_size=input_size, conf_threshold=conf_threshold)
            annotated = draw_detections(img, detections)
            out_path = annotated_dir / "result.jpg"
            cv2.imwrite(str(out_path), annotated)
            all_detections = [{"frame": 0, "detections": detections, "timings": timings}]
            task.progress = 100

        elif ext in {".mp4", ".avi", ".mov", ".mkv"}:
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
            "detections_summary": all_detections[:10],
            "device": device,
            "model_type": model_type,
        }
        db.commit()

    except Exception as e:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = "failed"
            task.error_msg = str(e)
            db.commit()
    finally:
        db.close()
