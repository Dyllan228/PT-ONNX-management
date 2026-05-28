import os
from sqlalchemy.orm import Session
from db.models import Model as ModelDB
from schemas.model_schema import ModelUpdate


def extract_model_metadata(pt_path: str) -> dict:
    """Extract metadata from a PyTorch model file."""
    metadata = {
        "param_count": None,
        "class_names": None,
        "input_size": None,
        "description": None,
    }
    try:
        import torch
        checkpoint = torch.load(pt_path, map_location="cpu", weights_only=False)

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

        if model is not None:
            if hasattr(model, "parameters"):
                try:
                    metadata["param_count"] = sum(p.numel() for p in model.parameters())
                except TypeError:
                    pass
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
    except Exception as e:
        metadata["description"] = f"元数据提取失败: {str(e)}"

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


def create_model(db: Session, name: str, version: str, pt_file_path: str,
                 file_size: int, **kwargs) -> ModelDB:
    metadata = extract_model_metadata(pt_file_path)
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
    return db.query(ModelDB).offset(skip).limit(limit).all()


def get_model(db: Session, model_id: int):
    return db.query(ModelDB).filter(ModelDB.id == model_id).first()


def update_model(db: Session, model_id: int, update: ModelUpdate):
    db_model = get_model(db, model_id)
    if not db_model:
        return None
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_model, key, value)
    db.commit()
    db.refresh(db_model)
    return db_model


def delete_model(db: Session, model_id: int):
    db_model = get_model(db, model_id)
    if not db_model:
        return False
    if os.path.exists(db_model.pt_file_path):
        os.remove(db_model.pt_file_path)
    if db_model.onnx_file_path and os.path.exists(db_model.onnx_file_path):
        os.remove(db_model.onnx_file_path)
    db.delete(db_model)
    db.commit()
    return True
