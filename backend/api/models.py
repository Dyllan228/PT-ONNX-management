"""
模型管理 API 模块

本模块提供模型文件的 CRUD 操作，包括：
1. 列出所有模型
2. 获取单个模型详情
3. 上传新模型
4. 更新模型信息
5. 删除模型
6. 扫描并注册新模型
7. 下载模型文件

路由前缀：/api/models
"""

import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.model_schema import ModelResponse, ModelUpdate
from services import model_service
from storage.file_manager import MODELS_PT_DIR, ensure_dirs

# 创建路由器，所有路由以 /api/models 开头
router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=List[ModelResponse])
def list_models(db: Session = Depends(get_db)):
    """
    获取所有模型列表

    返回：
    - List[ModelResponse]: 模型列表，包含所有模型的详细信息

    使用场景：
    - 模型管理页面展示
    - 模型选择下拉框
    """
    return model_service.get_models(db)


@router.get("/{model_id}", response_model=ModelResponse)
def get_model(model_id: int, db: Session = Depends(get_db)):
    """
    获取单个模型详情

    参数：
    - model_id: 模型 ID

    返回：
    - ModelResponse: 模型详细信息

    异常：
    - 404: 模型不存在
    """
    model = model_service.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.post("/upload", response_model=ModelResponse)
async def upload_model(
    file: UploadFile = File(...),      # 上传的文件
    name: str = Form(...),             # 模型名称
    version: str = Form("v1"),         # 版本号，默认 v1
    db: Session = Depends(get_db),     # 数据库会话
):
    """
    上传 PT 模型文件

    流程：
    1. 验证文件格式（仅支持 .pt）
    2. 生成唯一文件名（避免冲突）
    3. 保存文件到 storage/models/pt/
    4. 提取模型元数据（参数量、类别等）
    5. 注册到数据库

    参数：
    - file: 上传的 .pt 文件
    - name: 模型名称（如 "yolov8n"）
    - version: 版本号（如 "v1", "v2.0"）

    返回：
    - ModelResponse: 新创建的模型信息

    异常：
    - 400: 文件格式不支持或名称+版本重复
    """
    # 确保目录存在
    ensure_dirs()

    # 验证文件格式
    if not file.filename.endswith(".pt"):
        raise HTTPException(status_code=400, detail="Only .pt files are supported")

    # 生成唯一文件名：名称_版本_随机ID.pt
    filename = f"{name}_{version}_{uuid.uuid4().hex[:8]}.pt"
    file_path = MODELS_PT_DIR / filename

    # 保存文件
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    try:
        # 注册到数据库（会自动提取元数据）
        return model_service.create_model(
            db, name=name, version=version,
            pt_file_path=str(file_path), file_size=len(content),
        )
    except ValueError as e:
        # 如果注册失败（如名称重复），删除已保存的文件
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{model_id}", response_model=ModelResponse)
def update_model(model_id: int, update: ModelUpdate, db: Session = Depends(get_db)):
    """
    更新模型信息

    可更新字段：
    - name: 模型名称
    - version: 版本号
    - description: 模型描述
    - class_names: 类别名称
    - input_size: 输入尺寸
    - training_epochs: 训练轮数
    - training_samples: 训练样本数

    参数：
    - model_id: 模型 ID
    - update: 更新数据（仅包含需要更新的字段）

    返回：
    - ModelResponse: 更新后的模型信息

    异常：
    - 400: 名称+版本重复
    - 404: 模型不存在
    """
    try:
        model = model_service.update_model(db, model_id, update)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.delete("/{model_id}")
def delete_model(model_id: int, db: Session = Depends(get_db)):
    """
    删除模型

    会同时删除：
    - 数据库记录
    - PT 模型文件
    - ONNX 模型文件（如果存在）

    参数：
    - model_id: 模型 ID

    返回：
    - dict: {"success": true}

    异常：
    - 404: 模型不存在
    """
    success = model_service.delete_model(db, model_id)
    if not success:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"success": True}


@router.post("/scan")
def scan_models(db: Session = Depends(get_db)):
    """
    扫描并注册新模型

    扫描项目根目录和 storage/models/pt/ 目录，
    自动发现并注册新的 .pt 模型文件

    返回：
    - dict: {"scanned": 新注册的模型数量}
    """
    from services.scan_service import scan_and_register
    count = scan_and_register(db)
    return {"scanned": count}


@router.get("/{model_id}/download/{model_type}")
def download_model(model_id: int, model_type: str, db: Session = Depends(get_db)):
    """
    下载模型文件

    参数：
    - model_id: 模型 ID
    - model_type: 模型类型（"pt" 或 "onnx"）

    返回：
    - FileResponse: 文件下载响应

    异常：
    - 400: 无效的模型类型
    - 404: 模型或文件不存在
    """
    from fastapi.responses import FileResponse

    model = model_service.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    if model_type == "pt":
        # 下载 PT 模型
        if not model.pt_file_path or not os.path.exists(model.pt_file_path):
            raise HTTPException(status_code=404, detail="PT file not found")
        return FileResponse(
            model.pt_file_path,
            filename=f"{model.name}_{model.version}.pt"
        )
    elif model_type == "onnx":
        # 下载 ONNX 模型
        if not model.onnx_file_path or not os.path.exists(model.onnx_file_path):
            raise HTTPException(status_code=404, detail="ONNX file not found")
        return FileResponse(
            model.onnx_file_path,
            filename=f"{model.name}_{model.version}.onnx"
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid model type")
