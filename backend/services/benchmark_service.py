import os
import time
import cv2
import numpy as np
from db.database import SessionLocal
from db.models import Model as ModelDB, Task, BenchmarkRecord
from engines.pt_engine import PTEngine
from engines.onnx_engine import ONNXEngine


def run_benchmark(task_id: str, model_ids: list, model_types: list,
                  devices: list, data_path: str, input_size=(640, 640),
                  conf_threshold=0.5, num_runs=100):
    """Run benchmark comparing multiple models. Runs in background thread."""
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        task.status = "running"
        task.progress = 5
        db.commit()

        img = cv2.imread(data_path)
        if img is None:
            raise ValueError(f"Cannot read data file: {data_path}")

        results = []
        total_configs = len(model_ids) * max(len(devices), 1)
        config_idx = 0

        for model_id, model_type in zip(model_ids, model_types):
            model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
            if not model:
                continue

            for device in devices:
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
                import psutil
                process = psutil.Process()
                mem_before = process.memory_info().rss / (1024 * 1024)

                preprocess_times = []
                inference_times = []
                postprocess_times = []

                for run in range(num_runs):
                    _, timings = engine.infer(img, input_size=input_size, conf_threshold=conf_threshold)
                    preprocess_times.append(timings["preprocess_ms"])
                    inference_times.append(timings["inference_ms"])
                    postprocess_times.append(timings["postprocess_ms"])

                mem_after = process.memory_info().rss / (1024 * 1024)
                peak_memory = max(mem_before, mem_after)

                avg_preprocess = np.mean(preprocess_times)
                avg_inference = np.mean(inference_times)
                avg_postprocess = np.mean(postprocess_times)
                total_ms = avg_preprocess + avg_inference + avg_postprocess
                fps = 1000.0 / total_ms if total_ms > 0 else 0

                record = BenchmarkRecord(
                    task_id=task_id,
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

                config_idx += 1
                task.progress = min(99, int(5 + 90 * config_idx / total_configs))
                db.commit()

        task.progress = 100
        task.status = "completed"
        task.result = {"benchmarks": results}
        db.commit()

    except Exception as e:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = "failed"
            task.error_msg = str(e)
            db.commit()
    finally:
        db.close()
