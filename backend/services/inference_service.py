import os
import shutil
import cv2
import numpy as np
from pathlib import Path
from db.database import SessionLocal
from db.models import Model as ModelDB, Task
from engines.pt_engine import PTEngine
from engines.onnx_engine import ONNXEngine
from storage.file_manager import RESULTS_DIR

# 保留最近的结果数量
MAX_RESULTS_TO_KEEP = 5


def _cleanup_old_results(keep: int = MAX_RESULTS_TO_KEEP):
    """删除旧的推理结果目录，只保留最近 keep 次。"""
    if not RESULTS_DIR.exists():
        return
    # 按修改时间排序，最新的在前
    dirs = sorted(
        [d for d in RESULTS_DIR.iterdir() if d.is_dir()],
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )
    for old_dir in dirs[keep:]:
        try:
            shutil.rmtree(old_dir)
        except Exception:
            pass


def imread_safe(path):
    """支持中文路径的图片读取。"""
    data = np.fromfile(path, dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)

# 取消任务集合
_cancelled_tasks = set()

# 检测类别调色板 (BGR)
_CLASS_COLORS = [
    (0, 255, 0),     # 绿色
    (0, 165, 255),   # 橙色
    (0, 0, 255),     # 红色
    (255, 0, 0),     # 蓝色
    (255, 255, 0),   # 青色
    (0, 255, 255),   # 黄色
    (255, 0, 255),   # 品红
    (128, 0, 128),   # 紫色
    (0, 128, 255),   # 橙红
    (128, 128, 0),   # 橄榄
]


def _get_color(class_id: int):
    return _CLASS_COLORS[class_id % len(_CLASS_COLORS)]


def cancel_inference(task_id: str):
    _cancelled_tasks.add(task_id)


def _is_cancelled(task_id: str) -> bool:
    return task_id in _cancelled_tasks


def _cleanup_cancelled(task_id: str):
    _cancelled_tasks.discard(task_id)


def _update_progress(db, task, progress, msg):
    task.progress = progress
    result = task.result or {}
    result["_progress_msg"] = msg
    task.result = result
    db.commit()


def draw_detections(img, detections):
    """在图片上绘制检测框，不同类别使用不同颜色。"""
    for det in detections:
        x1, y1, x2, y2 = [int(v) for v in det["bbox"]]
        class_id = det.get("class_id", 0)
        color = _get_color(class_id)
        label = f"{det['class_name']} {det['confidence']:.2f}"

        # 绘制检测框
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

        # 绘制标签背景（提高可读性）
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        cv2.rectangle(img, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
        cv2.putText(img, label, (x1 + 2, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    return img


def _save_result_video(annotated_dir: Path, total_frames: int, fps: float, w: int, h: int) -> str:
    """将标注帧合成为 mp4 视频。"""
    video_path = annotated_dir / "result.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(video_path), fourcc, fps, (w, h))

    for i in range(total_frames):
        frame_path = annotated_dir / f"frame_{i:06d}.jpg"
        if frame_path.exists():
            frame = imread_safe(str(frame_path))
            if frame is not None:
                # 确保尺寸一致
                if frame.shape[1] != w or frame.shape[0] != h:
                    frame = cv2.resize(frame, (w, h))
                writer.write(frame)

    writer.release()
    return str(video_path) if video_path.exists() else None


def run_inference(model_id: int, task_id: str, model_type: str, device: str,
                  data_path: str, input_size=(640, 640), conf_threshold=0.5):
    """Run inference on image or video. Runs in background thread with own DB session."""
    db = SessionLocal()
    try:
        # 清理旧结果，只保留最近 N 次
        _cleanup_old_results()

        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        task = db.query(Task).filter(Task.id == task_id).first()

        task.status = "running"
        _update_progress(db, task, 2, "准备推理任务...")

        # 检查模型文件是否存在
        _update_progress(db, task, 5, f"检查{model_type.upper()}模型文件...")
        if model_type == "pt":
            if not model.pt_file_path or not os.path.exists(model.pt_file_path):
                raise FileNotFoundError(f"PT模型文件不存在: {model.pt_file_path}，请重新上传模型")
        else:
            if not model.onnx_file_path or not os.path.exists(model.onnx_file_path):
                raise FileNotFoundError(f"ONNX模型文件不存在: {model.onnx_file_path}，请先进行模型转换")

        # 加载模型
        _update_progress(db, task, 8, f"加载{model_type.upper()}模型中...")
        if model_type == "pt":
            engine = PTEngine(model.pt_file_path, device=device)
        else:
            engine = ONNXEngine(model.onnx_file_path, device=device)
            if model.class_names:
                engine.set_names({i: n for i, n in enumerate(model.class_names)})
        _update_progress(db, task, 12, f"{model_type.upper()}模型加载完成，设备: {device}")

        # 准备输出目录
        result_dir = RESULTS_DIR / task_id
        annotated_dir = result_dir / "annotated"
        annotated_dir.mkdir(parents=True, exist_ok=True)

        # 如果是目录，收集所有图片
        is_dataset_dir = False
        dataset_images = []
        if os.path.isdir(data_path):
            img_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
            for root, dirs, files in os.walk(data_path):
                for f in sorted(files):
                    if os.path.splitext(f)[1].lower() in img_exts:
                        dataset_images.append(os.path.join(root, f))
            if not dataset_images:
                raise ValueError(f"数据集目录中未找到图片: {data_path}")
            is_dataset_dir = True

        # 加载数据
        if is_dataset_dir:
            ext = ".jpg"  # 标记为图片类型处理
            _update_progress(db, task, 15, f"数据集已加载: {len(dataset_images)} 张图片")
        else:
            ext = Path(data_path).suffix.lower()
            _update_progress(db, task, 15, f"加载数据: {Path(data_path).name}")

        if _is_cancelled(task_id):
            task.status = "failed"
            task.error_msg = "用户终止"
            db.commit()
            return

        all_detections = []

        if is_dataset_dir:
            # 数据集目录：逐张图片推理，类似视频帧处理
            total_images = len(dataset_images)
            _update_progress(db, task, 15, f"开始逐帧推理: {total_images} 张图片")
            all_detections = []

            for frame_idx, img_path in enumerate(dataset_images):
                if _is_cancelled(task_id):
                    task.status = "failed"
                    task.error_msg = f"用户终止 (已处理 {frame_idx}/{total_images} 帧)"
                    _cleanup_cancelled(task_id)
                    db.commit()
                    return

                img = imread_safe(img_path)
                if img is None:
                    continue

                detections, timings = engine.infer(img, input_size=input_size, conf_threshold=conf_threshold)
                annotated = draw_detections(img.copy(), detections)
                out_path = annotated_dir / f"frame_{frame_idx:06d}.jpg"
                cv2.imwrite(str(out_path), annotated)

                all_detections.append({
                    "frame": frame_idx,
                    "detections": detections,
                    "timings": timings,
                    "filename": os.path.basename(img_path),
                })
                frame_idx += 1

                if total_images > 0:
                    pct = min(98, int(15 + 80 * frame_idx / total_images))
                    _update_progress(db, task, pct,
                        f"推理中: {frame_idx}/{total_images} 帧 | 检测 {len(detections)} 个目标")

                task.result = {
                    "annotated_dir": str(annotated_dir),
                    "total_frames": frame_idx,
                    "detections_summary": all_detections[-10:],
                    "device": device,
                    "model_type": model_type,
                    "_progress_msg": task.result.get("_progress_msg", "") if task.result else "",
                }
                db.commit()

            task.progress = 100
            task.status = "completed"
            task.result = {
                "annotated_dir": str(annotated_dir),
                "total_frames": len(all_detections),
                "detections_summary": all_detections[-20:],
                "device": device,
                "model_type": model_type,
            }
            db.commit()

        elif ext in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
            img = imread_safe(data_path)
            if img is None:
                raise ValueError(f"无法读取图片: {data_path}")
            h, w = img.shape[:2]
            _update_progress(db, task, 20, f"图片已加载 ({w}x{h})，开始推理...")

            detections, timings = engine.infer(img, input_size=input_size, conf_threshold=conf_threshold)
            _update_progress(db, task, 70, f"推理完成，检测到 {len(detections)} 个目标")

            annotated = draw_detections(img, detections)
            out_path = annotated_dir / "frame_000000.jpg"
            cv2.imwrite(str(out_path), annotated)
            all_detections = [{"frame": 0, "detections": detections, "timings": timings}]

            _update_progress(db, task, 95, "结果标注图已保存")
            task.progress = 100
            task.status = "completed"
            task.result = {
                "annotated_dir": str(annotated_dir),
                "total_frames": 1,
                "detections_summary": all_detections,
                "device": device,
                "model_type": model_type,
            }
            db.commit()

        elif ext in {".mp4", ".avi", ".mov", ".mkv"}:
            cap = cv2.VideoCapture(data_path)
            if not cap.isOpened():
                raise ValueError(f"无法打开视频: {data_path}")

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            if total_frames <= 0:
                total_frames = 0
                while True:
                    ret, _ = cap.read()
                    if not ret:
                        break
                    total_frames += 1
                cap.release()
                cap = cv2.VideoCapture(data_path)

            _update_progress(db, task, 15,
                f"视频已加载: {w}x{h}, {total_frames}帧, {fps:.1f}FPS，开始逐帧推理...")

            frame_idx = 0
            while cap.isOpened():
                if _is_cancelled(task_id):
                    cap.release()
                    task.status = "failed"
                    task.error_msg = f"用户终止 (已处理 {frame_idx}/{total_frames} 帧)"
                    _cleanup_cancelled(task_id)
                    db.commit()
                    return

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
                    pct = min(98, int(15 + 80 * frame_idx / total_frames))
                    det_count = len(detections)
                    _update_progress(db, task, pct,
                        f"推理中: {frame_idx}/{total_frames} 帧 | 当前帧检测 {det_count} 个目标")

                task.result = {
                    "annotated_dir": str(annotated_dir),
                    "total_frames": frame_idx,
                    "detections_summary": all_detections[-10:],
                    "device": device,
                    "model_type": model_type,
                    "_progress_msg": task.result.get("_progress_msg", "") if task.result else "",
                }
                db.commit()

            cap.release()

            if _is_cancelled(task_id):
                task.status = "failed"
                task.error_msg = f"用户终止 (已处理 {frame_idx}/{total_frames} 帧)"
                _cleanup_cancelled(task_id)
                db.commit()
                return

            # 合成结果视频
            _update_progress(db, task, 99, "正在合成结果视频...")
            video_path = _save_result_video(annotated_dir, frame_idx, fps, w, h)

            task.progress = 100
            task.status = "completed"
            task.result = {
                "annotated_dir": str(annotated_dir),
                "total_frames": frame_idx,
                "detections_summary": all_detections[-20:],
                "device": device,
                "model_type": model_type,
                "video_path": video_path,
            }
            db.commit()
        else:
            raise ValueError(f"不支持的文件类型: {ext}")

    except Exception as e:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = "failed"
            task.error_msg = str(e)
            db.commit()
    finally:
        _cleanup_cancelled(task_id)
        db.close()
