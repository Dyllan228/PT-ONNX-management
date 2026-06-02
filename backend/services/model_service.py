"""
模型服务模块

本模块提供模型管理的业务逻辑，包括：
1. 模型元数据提取（参数量、类别名称等）
2. 模型 CRUD 操作
3. 名称+版本唯一性检查

技术说明：
- 自动从 PT 文件提取元数据
- 支持多种模型格式（Ultralytics、自定义）
- 事务性操作确保数据一致性
"""

import os
from sqlalchemy.orm import Session
from db.models import Model as ModelDB
from schemas.model_schema import ModelUpdate


def extract_model_metadata(pt_path: str) -> dict:
    """
    从 PyTorch 模型文件提取元数据

    支持提取的信息：
    - 参数量（param_count）
    - 类别名称（class_names）
    - 自动生成描述（description）

    支持的模型格式：
    - Ultralytics YOLO 格式
    - 标准 PyTorch 模型
    - 包含 state_dict 的检查点

    参数：
    - pt_path: PT 模型文件路径

    返回：
    - dict: 包含 param_count、class_names、description 的字典
    """
    metadata = {
        "param_count": None,
        "class_names": None,
        "input_size": None,
        "description": None,
    }

    try:
        import torch

        # 尝试导入 ultralytics（可选依赖）
        try:
            from ultralytics import YOLO
        except ImportError:
            pass

        # 加载模型检查点
        checkpoint = torch.load(pt_path, map_location="cpu", weights_only=False)

        # 解析模型结构
        model = None
        if isinstance(checkpoint, dict):
            if "model" in checkpoint:
                model = checkpoint["model"]
            elif "state_dict" in checkpoint:
                model = checkpoint["state_dict"]
        elif hasattr(checkpoint, "model"):
            model = checkpoint.model
        else:
            model = checkpoint

        # 提取参数量和类别名称
        if model is not None:
            if hasattr(model, "parameters"):
                try:
                    metadata["param_count"] = sum(p.numel() for p in model.parameters())
                except TypeError:
                    pass

            # 提取类别名称
            names = None
            if hasattr(checkpoint, "names"):
                names = checkpoint.names
            elif hasattr(model, "names"):
                names = model.names
            if names:
                if isinstance(names, list):
                    metadata["class_names"] = names
                elif isinstance(names, dict):
                    metadata["class_names"] = list(names.values())

    except ImportError as e:
        # 缺少可选依赖（如 ultralytics）
        metadata["description"] = f"元数据提取跳过 (缺少可选依赖: {str(e).split(':')[-1].strip()})"
    except Exception as e:
        err_msg = str(e)
        if "ultralytics" in err_msg.lower():
            metadata["description"] = "元数据提取跳过 (缺少 ultralytics，可通过 pip install ultralytics 安装)"
        else:
            metadata["description"] = f"元数据提取失败: {err_msg}"

    # 自动生成描述文本
    parts = []
    if metadata["param_count"]:
        pc = metadata["param_count"]
        parts.append(f"参数量: {pc / 1_000_000:.1f}M" if pc > 1_000_000 else f"参数量: {pc / 1_000:.1f}K")
    if metadata["class_names"]:
        parts.append(f"类别数: {len(metadata['class_names'])}")
        parts.append(f"类别: {', '.join(metadata['class_names'])}")
    if parts:
        metadata["description"] = " | ".join(parts)

    return metadata


def check_name_version_exists(db: Session, name: str, version: str, exclude_id: int = None):
    """
    检查名称+版本是否已存在

    参数：
    - db: 数据库会话
    - name: 模型名称
    - version: 版本号
    - exclude_id: 排除的模型 ID（更新时使用）

    返回：
    - bool: 是否存在重复
    """
    query = db.query(ModelDB).filter(ModelDB.name == name, ModelDB.version == version)
    if exclude_id:
        query = query.filter(ModelDB.id != exclude_id)
    return query.first() is not None


def create_model(db: Session, name: str, version: str, pt_file_path: str,
                 file_size: int, **kwargs) -> ModelDB:
    """
    创建新模型记录

    流程：
    1. 检查名称+版本唯一性
    2. 提取模型元数据
    3. 创建数据库记录

    参数：
    - db: 数据库会话
    - name: 模型名称
    - version: 版本号
    - pt_file_path: PT 文件路径
    - file_size: 文件大小（字节）
    - **kwargs: 其他字段

    返回：
    - ModelDB: 新创建的模型记录

    异常：
    - ValueError: 名称+版本重复
    """
    # 检查唯一性
    if check_name_version_exists(db, name, version):
        raise ValueError(f"模型 '{name}' 版本 '{version}' 已存在")

    # 提取元数据
    metadata = extract_model_metadata(pt_file_path)

    # 创建记录
    db_model = ModelDB(
        name=name,
        version=version,
        pt_file_path=pt_file_path,
        pt_file_size=file_size,
        description=metadata.get("description"),
        param_count=metadata.get("param_count"),
        class_names=metadata.get("class_names"),
        **kwargs,
    )
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model


def get_models(db: Session, skip: int = 0, limit: int = 100):
    """
    获取模型列表

    参数：
    - db: 数据库会话
    - skip: 跳过数量（分页）
    - limit: 返回数量（分页）

    返回：
    - List[ModelDB]: 模型列表
    """
    return db.query(ModelDB).offset(skip).limit(limit).all()


def get_model(db: Session, model_id: int):
    """
    获取单个模型

    参数：
    - db: 数据库会话
    - model_id: 模型 ID

    返回：
    - ModelDB: 模型记录（不存在返回 None）
    """
    return db.query(ModelDB).filter(ModelDB.id == model_id).first()


def update_model(db: Session, model_id: int, update: ModelUpdate):
    """
    更新模型信息

    参数：
    - db: 数据库会话
    - model_id: 模型 ID
    - update: 更新数据

    返回：
    - ModelDB: 更新后的模型记录（不存在返回 None）

    异常：
    - ValueError: 名称+版本重复
    """
    db_model = get_model(db, model_id)
    if not db_model:
        return None

    # 获取更新数据（仅包含用户设置的字段）
    update_data = update.model_dump(exclude_unset=True)

    # 检查名称+版本唯一性
    new_name = update_data.get("name", db_model.name)
    new_version = update_data.get("version", db_model.version)
    if "name" in update_data or "version" in update_data:
        if check_name_version_exists(db, new_name, new_version, exclude_id=model_id):
            raise ValueError(f"模型 '{new_name}' 版本 '{new_version}' 已存在")

    # 应用更新
    for key, value in update_data.items():
        setattr(db_model, key, value)

    db.commit()
    db.refresh(db_model)
    return db_model


def delete_model(db: Session, model_id: int):
    """
    删除模型

    会同时删除：
    - 数据库记录
    - PT 模型文件
    - ONNX 模型文件（如果存在）

    参数：
    - db: 数据库会话
    - model_id: 模型 ID

    返回：
    - bool: 是否成功删除
    """
    db_model = get_model(db, model_id)
    if not db_model:
        return False

    # 删除文件
    if os.path.exists(db_model.pt_file_path):
        os.remove(db_model.pt_file_path)
    if db_model.onnx_file_path and os.path.exists(db_model.onnx_file_path):
        os.remove(db_model.onnx_file_path)

    # 删除数据库记录
    db.delete(db_model)
    db.commit()
    return True
