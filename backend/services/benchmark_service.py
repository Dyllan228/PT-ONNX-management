import os
import time
import cv2
import numpy as np
from db.database import SessionLocal
from db.models import Model as ModelDB, Task, BenchmarkRecord
from engines.pt_engine import PTEngine
from engines.onnx_engine import ONNXEngine
from services.dataset_service import (
    detect_splits, get_split_images, get_label_path, read_labels,
    compute_detection_metrics,
)
from storage.file_manager import BASE_DIR


def imread_safe(path):
    """支持中文路径的图片读取。"""
    data = np.fromfile(path, dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def _update_progress(db, task, progress, msg):
    task.progress = progress
    result = task.result or {}
    result["_progress_msg"] = msg
    task.result = result
    db.commit()


def run_benchmark(task_id: str, model_ids: list, model_types: list,
                  devices: list, data_path: str = None, dataset_split: str = None,
                  input_size=(640, 640), conf_threshold=0.5, num_runs=100,
                  evaluate: bool = False):
    """Run benchmark. Supports speed test and accuracy evaluation."""
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        task.status = "running"
        _update_progress(db, task, 2, "准备测试数据...")

        # 确定测试图片
        if data_path and os.path.isdir(data_path):
            # 数据集目录
            images = get_split_images(data_path, dataset_split)
            if not images:
                raise ValueError("数据集中未找到图片")
            test_images = images[:min(len(images), 50)]  # 最多用 50 张
            img = imread_safe(test_images[0])
            data_source = "dataset"
            _update_progress(db, task, 5,
                f"数据集模式: {len(test_images)} 张图片 (split: {dataset_split or 'auto'})")
        elif data_path and os.path.isfile(data_path):
            ext = os.path.splitext(data_path)[1].lower()
            if ext in {".mp4", ".avi", ".mov", ".mkv"}:
                cap = cv2.VideoCapture(data_path)
                ret, img = cap.read()
                cap.release()
                if not ret or img is None:
                    raise ValueError(f"无法读取视频: {data_path}")
            else:
                img = imread_safe(data_path)
                if img is None:
                    raise ValueError(f"无法读取文件: {data_path}")
            test_images = [data_path]
            data_source = "file"
        else:
            # 默认视频
            default_path = str(BASE_DIR / "反光衣测试.mp4")
            cap = cv2.VideoCapture(default_path)
            ret, img = cap.read()
            cap.release()
            if not ret or img is None:
                raise ValueError("无法读取默认测试视频")
            test_images = [default_path]
            data_source = "file"

        if img is None:
            raise ValueError("无法读取测试数据")

        results = []
        total_configs = len(model_ids) * max(len(devices), 1)
        config_idx = 0

        for model_id, model_type in zip(model_ids, model_types):
            model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
            if not model:
                continue

            for device in devices:
                config_idx += 1
                config_label = f"{model.name} {model.version} ({model_type.upper()}) / {device.upper()}"

                _update_progress(db, task,
                    min(5 + int(90 * (config_idx - 1) / total_configs), 95),
                    f"[{config_idx}/{total_configs}] 加载模型: {config_label}")

                if model_type == "pt":
                    engine = PTEngine(model.pt_file_path, device=device)
                    model_file_size = model.pt_file_size or os.path.getsize(model.pt_file_path)
                else:
                    engine = ONNXEngine(model.onnx_file_path, device=device)
                    model_file_size = model.onnx_file_size or os.path.getsize(model.onnx_file_path)
                    if model.class_names:
                        engine.set_names({i: n for i, n in enumerate(model.class_names)})

                # 预热
                _update_progress(db, task, task.progress, f"[{config_idx}/{total_configs}] 预热中")
                for _ in range(3):
                    engine.infer(img, input_size=input_size, conf_threshold=conf_threshold)

                # 速度测试
                _update_progress(db, task, task.progress,
                    f"[{config_idx}/{total_configs}] 速度测试: {num_runs} 次推理")
                import psutil
                process = psutil.Process()
                mem_before = process.memory_info().rss / (1024 * 1024)

                preprocess_times, inference_times, postprocess_times = [], [], []
                for run in range(num_runs):
                    _, timings = engine.infer(img, input_size=input_size, conf_threshold=conf_threshold)
                    preprocess_times.append(timings["preprocess_ms"])
                    inference_times.append(timings["inference_ms"])
                    postprocess_times.append(timings["postprocess_ms"])

                mem_after = process.memory_info().rss / (1024 * 1024)
                avg_preprocess = np.mean(preprocess_times)
                avg_inference = np.mean(inference_times)
                avg_postprocess = np.mean(postprocess_times)
                total_ms = avg_preprocess + avg_inference + avg_postprocess
                fps = 1000.0 / total_ms if total_ms > 0 else 0

                # 准确度评估
                eval_metrics = None
                if evaluate and data_source == "dataset" and model.class_names:
                    _update_progress(db, task, task.progress,
                        f"[{config_idx}/{total_configs}] 评估准确度: {len(test_images)} 张图片")

                    names = {i: n for i, n in enumerate(model.class_names)}
                    all_dets, all_gts = [], []

                    for img_path in test_images:
                        frame = imread_safe(img_path)
                        if frame is None:
                            continue
                        dets, _ = engine.infer(frame, input_size=input_size, conf_threshold=conf_threshold)
                        h, w = frame.shape[:2]
                        all_dets.append(dets)

                        # 读取 ground truth
                        label_path = get_label_path(img_path)
                        raw_labels = read_labels(label_path)
                        # 转换 YOLO 归一化坐标为 xyxy 像素坐标
                        gts = []
                        for lb in raw_labels:
                            cx, cy = lb["cx"], lb["cy"]
                            bw, bh = lb["w"], lb["h"]
                            gts.append({
                                "class_id": lb["class_id"],
                                "bbox": [
                                    (cx - bw / 2) * w, (cy - bh / 2) * h,
                                    (cx + bw / 2) * w, (cy + bh / 2) * h,
                                ],
                            })
                        all_gts.append(gts)

                    eval_metrics = compute_detection_metrics(all_dets, all_gts, names)

                # 保存记录
                record = BenchmarkRecord(
                    task_id=task_id, model_id=model_id, model_type=model_type, device=device,
                    avg_inference_ms=round(avg_inference, 2),
                    avg_preprocess_ms=round(avg_preprocess, 2),
                    avg_postprocess_ms=round(avg_postprocess, 2),
                    peak_memory_mb=round(max(mem_before, mem_after), 2),
                    model_size_mb=round(model_file_size / (1024 * 1024), 2),
                    fps=round(fps, 2),
                    precision_metrics={"num_runs": num_runs, "std_inference_ms": round(np.std(inference_times), 2)},
                )
                db.add(record)

                result_entry = {
                    "model_id": model_id,
                    "model_name": model.name,
                    "model_version": model.version,
                    "model_type": model_type,
                    "device": device,
                    "avg_inference_ms": round(avg_inference, 2),
                    "avg_preprocess_ms": round(avg_preprocess, 2),
                    "avg_postprocess_ms": round(avg_postprocess, 2),
                    "fps": round(fps, 2),
                    "peak_memory_mb": round(max(mem_before, mem_after), 2),
                    "model_size_mb": round(model_file_size / (1024 * 1024), 2),
                }
                if eval_metrics:
                    result_entry["precision"] = eval_metrics["precision"]
                    result_entry["recall"] = eval_metrics["recall"]
                    result_entry["f1"] = eval_metrics["f1"]
                    result_entry["mAP"] = eval_metrics["mAP@0.5"]
                    result_entry["per_class"] = eval_metrics["per_class"]
                    result_entry["total_gt"] = eval_metrics["total_gt"]
                    result_entry["total_det"] = eval_metrics["total_det"]

                results.append(result_entry)

                pct = min(95, int(5 + 90 * config_idx / total_configs))
                _update_progress(db, task, pct, f"[{config_idx}/{total_configs}] {config_label} 完成")

        _update_progress(db, task, 99, "整理测试结果...")
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
