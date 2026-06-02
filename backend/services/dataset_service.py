import os
import zipfile
import shutil
import io
import numpy as np
from pathlib import Path
from sqlalchemy.orm import Session
from db.models import Dataset as DatasetDB

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
LABEL_EXTS = {".txt"}


def analyze_dataset(zip_path: str, extract_dir: str) -> dict:
    """解压并分析目标检测数据集 ZIP 包。"""
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_dir)

    # 检测子集结构
    splits = detect_splits(extract_dir)

    # 全局统计
    image_files = []
    label_files = []
    for root, dirs, files in os.walk(extract_dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            full_path = os.path.join(root, f)
            if ext in IMAGE_EXTS:
                image_files.append(full_path)
            elif ext in LABEL_EXTS:
                label_files.append(full_path)

    label_map = {Path(lp).stem: lp for lp in label_files}

    class_counts = {}
    total_labels = 0
    images_with_labels = 0

    for img_path in image_files:
        stem = Path(img_path).stem
        if stem in label_map:
            images_with_labels += 1
            try:
                with open(label_map[stem], 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        parts = line.split()
                        if len(parts) >= 1:
                            class_counts[parts[0]] = class_counts.get(parts[0], 0) + 1
                            total_labels += 1
            except Exception:
                pass

    class_names = _read_class_names(extract_dir)

    distribution = {}
    for cid, count in class_counts.items():
        name = class_names.get(cid, f"class_{cid}")
        distribution[name] = count
    distribution = dict(sorted(distribution.items(), key=lambda x: -x[1]))

    # 每个子集的统计
    split_stats = {}
    for split_name, split_dir in splits.items():
        split_imgs = []
        split_labels = []
        for root, dirs, files in os.walk(split_dir):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in IMAGE_EXTS:
                    split_imgs.append(f)
                elif ext in LABEL_EXTS:
                    split_labels.append(f)
        split_stats[split_name] = {"images": len(split_imgs), "labels": len(split_labels)}

    return {
        "image_count": len(image_files),
        "label_count": images_with_labels,
        "total_objects": total_labels,
        "class_names": list(distribution.keys()),
        "class_distribution": distribution,
        "splits": list(splits.keys()),
        "split_stats": split_stats,
    }


def detect_splits(dataset_dir: str) -> dict:
    """检测数据集的子集结构 (train/test/val)。"""
    splits = {}
    standard_names = {"train", "test", "val", "valid", "validation"}

    for item in os.listdir(dataset_dir):
        item_path = os.path.join(dataset_dir, item)
        if not os.path.isdir(item_path):
            continue
        name_lower = item.lower()
        if name_lower in standard_names:
            canonical = "val" if name_lower in ("valid", "validation") else name_lower
            splits[canonical] = item_path

    # 检查 images/ 子目录下的 splits
    images_dir = os.path.join(dataset_dir, "images")
    if os.path.isdir(images_dir):
        for item in os.listdir(images_dir):
            item_path = os.path.join(images_dir, item)
            if not os.path.isdir(item_path):
                continue
            name_lower = item.lower()
            if name_lower in standard_names:
                canonical = "val" if name_lower in ("valid", "validation") else name_lower
                splits[canonical] = item_path

    return splits


def get_split_images(dataset_path: str, split: str = None) -> list:
    """获取数据集指定子集的图片路径列表。"""
    splits = detect_splits(dataset_path)

    if split and split in splits:
        base_dir = splits[split]
    elif splits:
        base_dir = splits.get("test") or splits.get("val") or list(splits.values())[0]
    else:
        base_dir = dataset_path

    images = []
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            if os.path.splitext(f)[1].lower() in IMAGE_EXTS:
                images.append(os.path.join(root, f))

    # 如果在 split 目录下找不到，尝试从 labels 同级的 images 目录找
    if not images and os.path.isdir(os.path.join(dataset_path, "images")):
        img_base = os.path.join(dataset_path, "images", split) if split else os.path.join(dataset_path, "images")
        if os.path.isdir(img_base):
            for f in os.listdir(img_base):
                if os.path.splitext(f)[1].lower() in IMAGE_EXTS:
                    images.append(os.path.join(img_base, f))

    return sorted(images)


def get_label_path(image_path: str) -> str:
    """根据图片路径推导对应的标注文件路径。"""
    stem = Path(image_path).stem
    parent = Path(image_path).parent

    # 同目录
    label = parent / f"{stem}.txt"
    if label.exists():
        return str(label)

    # labels/ 同级目录
    labels_dir = parent.parent / "labels" / parent.name
    label = labels_dir / f"{stem}.txt"
    if label.exists():
        return str(label)

    # labels/ 在 parent 的同级
    labels_dir = parent.parent / "labels"
    label = labels_dir / f"{stem}.txt"
    if label.exists():
        return str(label)

    return None


def read_labels(label_path: str, img_w: int = None, img_h: int = None) -> list:
    """读取 YOLO 格式标注文件。返回 [{class_id, cx, cy, w, h}]"""
    if not label_path or not os.path.exists(label_path):
        return []
    labels = []
    try:
        with open(label_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    labels.append({
                        "class_id": int(parts[0]),
                        "cx": float(parts[1]),
                        "cy": float(parts[2]),
                        "w": float(parts[3]),
                        "h": float(parts[4]),
                    })
    except Exception:
        pass
    return labels


def compute_iou(box1, box2):
    """计算两个 xyxy 格式框的 IoU。"""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - inter
    return inter / union if union > 0 else 0


def compute_detection_metrics(detections_list: list, ground_truth_list: list,
                              class_names: dict, iou_thresholds: list = None) -> dict:
    """计算目标检测指标。

    Args:
        detections_list: [{class_id, confidence, bbox:[x1,y1,x2,y2]}, ...] per image
        ground_truth_list: [{class_id, cx, cy, w, h}, ...] per image (YOLO归一化坐标)
        class_names: {id: name}
        iou_thresholds: IoU 阈值列表，默认 [0.5]

    Returns:
        {precision, recall, f1, mAP, per_class_metrics}
    """
    if iou_thresholds is None:
        iou_thresholds = [0.5]

    class_ids = set()
    for gt_list in ground_truth_list:
        for gt in gt_list:
            class_ids.add(gt["class_id"])

    per_class = {}
    for cid in class_ids:
        per_class[cid] = {"tp": 0, "fp": 0, "fn": 0}

    for dets, gts in zip(detections_list, ground_truth_list):
        # 按 class_id 分组
        gt_by_class = {}
        for gt in gts:
            gt_by_class.setdefault(gt["class_id"], []).append(gt)

        det_by_class = {}
        for det in dets:
            det_by_class.setdefault(det["class_id"], []).append(det)

        for cid in class_ids:
            gt_list = gt_by_class.get(cid, [])
            det_list = sorted(det_by_class.get(cid, []), key=lambda x: -x["confidence"])

            matched_gt = set()
            for det in det_list:
                best_iou = 0
                best_idx = -1
                for i, gt in enumerate(gt_list):
                    if i in matched_gt:
                        continue
                    iou = compute_iou(det["bbox"], gt["bbox"])
                    if iou > best_iou:
                        best_iou = iou
                        best_idx = i
                if best_iou >= iou_thresholds[0] and best_idx >= 0:
                    matched_gt.add(best_idx)
                    per_class[cid]["tp"] += 1
                else:
                    per_class[cid]["fp"] += 1
            per_class[cid]["fn"] += len(gt_list) - len(matched_gt)

    # 汇总
    total_tp = sum(v["tp"] for v in per_class.values())
    total_fp = sum(v["fp"] for v in per_class.values())
    total_fn = sum(v["fn"] for v in per_class.values())

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    # 每个类别的指标
    class_metrics = {}
    for cid, counts in per_class.items():
        tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
        cp = tp / (tp + fp) if (tp + fp) > 0 else 0
        cr = tp / (tp + fn) if (tp + fn) > 0 else 0
        cf1 = 2 * cp * cr / (cp + cr) if (cp + cr) > 0 else 0
        name = class_names.get(cid, f"class_{cid}")
        class_metrics[name] = {"precision": round(cp, 4), "recall": round(cr, 4), "f1": round(cf1, 4), "count": tp + fn}

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "mAP@0.5": round(precision, 4),  # 简化：IoU=0.5 时的 precision 作为 mAP@0.5
        "per_class": class_metrics,
        "total_gt": total_tp + total_fn,
        "total_det": total_tp + total_fp,
    }


def _read_class_names(extract_dir: str) -> dict:
    """读取类别名称，支持 classes.txt 和 data.yaml/data.yml。"""
    class_names = {}

    for root, dirs, files in os.walk(extract_dir):
        # 优先读取 data.yaml / data.yml
        for yaml_name in ("data.yaml", "data.yml", "dataset.yaml", "dataset.yml"):
            if yaml_name in files:
                names = _parse_yaml_names(os.path.join(root, yaml_name))
                if names:
                    return names

        # 其次读取 classes.txt
        if "classes.txt" in files:
            try:
                with open(os.path.join(root, "classes.txt"), 'r', encoding='utf-8', errors='ignore') as f:
                    for i, line in enumerate(f):
                        name = line.strip()
                        if name:
                            class_names[str(i)] = name
            except Exception:
                pass
            return class_names

    return class_names


def _parse_yaml_names(yaml_path: str) -> dict:
    """简单解析 YOLO data.yaml 中的 names 字段。"""
    try:
        with open(yaml_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # 查找 names 字段
        lines = content.split('\n')
        in_names = False
        names = {}

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('names:'):
                # 同行: names: [helmet, vest] 或 names: {0: helmet, 1: vest}
                after = stripped[6:].strip()
                if after.startswith('['):
                    # 列表格式
                    items = after.strip('[]').split(',')
                    for i, item in enumerate(items):
                        name = item.strip().strip("'\"")
                        if name:
                            names[str(i)] = name
                    return names
                elif after.startswith('{'):
                    # 字典格式
                    items = after.strip('{}').split(',')
                    for item in items:
                        if ':' in item:
                            k, v = item.split(':', 1)
                            k = k.strip()
                            v = v.strip().strip("'\"")
                            # 支持整数key，统一转为字符串
                            try:
                                k = str(int(k))
                            except ValueError:
                                pass
                            if v:
                                names[k] = v
                    return names
                elif not after:
                    # 下一行开始的缩进格式
                    in_names = True
                continue

            if in_names:
                if stripped and ':' in stripped and not stripped.startswith('#'):
                    k, v = stripped.split(':', 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    # 支持整数key，统一转为字符串
                    try:
                        k = str(int(k))
                    except ValueError:
                        pass
                    if v:
                        names[k] = v
                elif not stripped.startswith('#') and stripped and not line.startswith(' '):
                    break

        return names
    except Exception:
        return {}


def create_dataset(db: Session, name: str, description: str, zip_path: str) -> DatasetDB:
    from storage.file_manager import STORAGE_DIR

    ds_id_placeholder = name.replace(" ", "_")
    extract_dir = str(STORAGE_DIR / "datasets" / ds_id_placeholder)
    os.makedirs(extract_dir, exist_ok=True)

    info = analyze_dataset(zip_path, extract_dir)
    file_size = os.path.getsize(zip_path)

    db_ds = DatasetDB(
        name=name,
        description=description,
        path=extract_dir,
        file_size=file_size,
        image_count=info["image_count"],
        label_count=info["label_count"],
        class_names=info["class_names"],
        class_distribution=info["class_distribution"],
    )
    db.add(db_ds)
    db.commit()
    db.refresh(db_ds)

    real_dir = str(STORAGE_DIR / "datasets" / str(db_ds.id))
    if os.path.exists(real_dir):
        shutil.rmtree(real_dir)
    os.rename(extract_dir, real_dir)
    db_ds.path = real_dir
    db.commit()

    return db_ds


def get_datasets(db: Session):
    return db.query(DatasetDB).order_by(DatasetDB.created_at.desc()).all()


def get_dataset(db: Session, dataset_id: int):
    return db.query(DatasetDB).filter(DatasetDB.id == dataset_id).first()


def update_dataset(db: Session, dataset_id: int, name: str = None, description: str = None):
    ds = get_dataset(db, dataset_id)
    if not ds:
        return None
    if name is not None:
        ds.name = name
    if description is not None:
        ds.description = description
    db.commit()
    db.refresh(ds)
    return ds


def delete_dataset(db: Session, dataset_id: int):
    ds = get_dataset(db, dataset_id)
    if not ds:
        return False
    if os.path.exists(ds.path):
        shutil.rmtree(ds.path)
    db.delete(ds)
    db.commit()
    return True


def create_zip(dataset_path: str) -> bytes:
    """将数据集目录打包为 ZIP，返回字节流。"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(dataset_path):
            for f in files:
                full_path = os.path.join(root, f)
                arcname = os.path.relpath(full_path, dataset_path)
                zf.write(full_path, arcname)
    return buf.getvalue()
