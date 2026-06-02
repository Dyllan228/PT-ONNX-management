"""
模型扫描服务模块

本模块提供自动扫描和注册模型的功能，包括：
1. 递归扫描目录中的 .pt 文件
2. 自动提取模型元数据
3. 注册到数据库
4. 清理无效记录
5. 关联已有的 ONNX 文件

扫描位置：
- 项目根目录（预置模型）
- storage/models/pt/（上传的模型）

命名规则：
- 文件名格式：{name}-{version}.pt（如 helmet-vest-v1.pt）
- 无版本号时默认为 v1
"""

import os
from pathlib import Path
from sqlalchemy.orm import Session
from db.models import Model as ModelDB
from services.model_service import extract_model_metadata
from storage.file_manager import BASE_DIR, MODELS_PT_DIR, MODELS_ONNX_DIR, ensure_dirs

SUPPORTED_PT_EXT = {".pt"}


def _cleanup_invalid_models(db: Session) -> int:
    """
    清理无效的模型记录

    删除数据库中文件已不存在的记录

    参数：
    - db: 数据库会话

    返回：
    - int: 删除的记录数
    """
    removed = 0
    for model in db.query(ModelDB).all():
        pt_exists = model.pt_file_path and os.path.exists(model.pt_file_path)
        onnx_exists = model.onnx_file_path and os.path.exists(model.onnx_file_path)

        # 如果 PT 文件不存在，删除整个记录
        if not pt_exists:
            db.delete(model)
            removed += 1
        # 如果只是 ONNX 文件不存在，更新状态
        elif not onnx_exists and model.onnx_converted:
            model.onnx_converted = False
            model.onnx_file_path = None
            model.onnx_file_size = None

    if removed:
        db.commit()
    return removed


def scan_and_register(db: Session) -> int:
    """
    扫描目录并注册新模型

    扫描流程：
    1. 确保目录存在
    2. 清理无效记录
    3. 递归扫描 .pt 文件
    4. 解析文件名（名称-版本）
    5. 提取元数据
    6. 注册到数据库
    7. 关联已有的 ONNX 文件

    参数：
    - db: 数据库会话

    返回：
    - int: 新注册的模型数量
    """
    ensure_dirs()
    count = 0

    # 清理无效记录
    removed = _cleanup_invalid_models(db)
    if removed:
        print(f"清理了 {removed} 个无效模型记录")

    # 获取已注册的路径和名称-版本组合
    registered_paths = {m.pt_file_path for m in db.query(ModelDB).all()}
    registered_name_versions = {(m.name, m.version) for m in db.query(ModelDB).all()}

    # 扫描目录列表
    scan_dirs = [BASE_DIR, MODELS_PT_DIR]

    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue

        # 递归扫描所有 .pt 文件
        for root, dirs, files in os.walk(str(scan_dir)):
            for fname in files:
                if not fname.lower().endswith(".pt"):
                    continue

                abs_path = str(Path(root, fname).resolve())
                if abs_path in registered_paths:
                    continue

                # 解析文件名（格式：name-version.pt）
                stem = Path(fname).stem
                name = stem.rsplit("-", 1)[0] if "-v" in stem else stem
                version = stem.rsplit("-", 1)[-1] if "-v" in stem else "v1"

                if (name, version) in registered_name_versions:
                    continue

                # 提取元数据
                try:
                    metadata = extract_model_metadata(abs_path)
                    file_size = os.path.getsize(abs_path)
                except Exception:
                    metadata = {}
                    file_size = 0

                # 创建数据库记录
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
                registered_name_versions.add((name, version))

    # 扫描已有的 ONNX 文件并关联
    for model in db.query(ModelDB).filter(ModelDB.onnx_converted == False).all():
        pt_path = Path(model.pt_file_path)
        # 在 MODELS_ONNX_DIR 中查找同名 ONNX
        onnx_path = MODELS_ONNX_DIR / (pt_path.stem + ".onnx")
        if not onnx_path.exists():
            # 也检查同目录
            onnx_path = pt_path.with_suffix(".onnx")
        if onnx_path.exists():
            model.onnx_file_path = str(onnx_path)
            model.onnx_converted = True
            model.onnx_file_size = onnx_path.stat().st_size

    db.commit()
    return count
