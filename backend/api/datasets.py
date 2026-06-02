"""
数据集管理 API 模块

本模块提供数据集管理功能，包括：
1. 数据源文件列表（供推理/性能对比选择）
2. 单文件上传（图片/视频）
3. 数据集导入（ZIP 格式，支持 YOLO 格式）
4. 数据集 CRUD 操作
5. 数据集下载
6. 数据集子集检测

路由前缀：/api/datasets

支持的数据集格式：
- YOLO 格式：images/ + labels/ 目录结构
- 标注文件：.txt 格式（class_id cx cy w h）
- 类别定义：classes.txt 或 data.yaml
"""

import uuid
import os
import tempfile
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db.database import get_db
from db.models import Dataset as DatasetDB
from services import dataset_service
from storage.file_manager import (
    UPLOADS_IMAGES_DIR, UPLOADS_VIDEOS_DIR,
    get_root_media_files, SUPPORTED_IMAGE_EXT, SUPPORTED_VIDEO_EXT, ensure_dirs,
)

# 创建路由器
router = APIRouter(prefix="/api/datasets", tags=["datasets"])


# ====== 简单数据源列表（供推理/性能对比使用） ======

@router.get("/sources")
def list_data_sources():
    """
    列出可用的数据源文件

    扫描位置：
    1. 项目根目录（预置的测试文件）
    2. 上传目录（用户上传的文件）

    返回：
    - id: 数据源 ID
    - name: 文件名
    - path: 文件路径
    - type: 类型（image/video）
    - size_mb: 文件大小（MB）
    - source: 来源（root/upload）
    """
    ensure_dirs()
    sources = []

    # 扫描项目根目录
    for f in get_root_media_files():
        ext = f.suffix.lower()
        dtype = "image" if ext in SUPPORTED_IMAGE_EXT else "video"
        sources.append({
            "id": f"root_{f.stem}",
            "name": f.name,
            "path": str(f),
            "type": dtype,
            "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
            "source": "root",
        })

    # 扫描上传目录
    for d, dtype in [(UPLOADS_IMAGES_DIR, "image"), (UPLOADS_VIDEOS_DIR, "video")]:
        if d.exists():
            for f in d.iterdir():
                if f.is_file():
                    sources.append({
                        "id": f"upload_{f.stem}",
                        "name": f.name,
                        "path": str(f),
                        "type": dtype,
                        "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                        "source": "upload",
                    })

    return sources


@router.post("/upload")
async def upload_data_source(file: UploadFile = File(...)):
    """
    上传单个数据文件（图片/视频）

    用于推理时上传临时测试文件

    参数：
    - file: 上传的文件（支持 jpg/jpeg/png/bmp/webp/mp4/avi/mov/mkv）

    返回：
    - id: 数据源 ID
    - name: 原始文件名
    - path: 保存路径
    - type: 类型（image/video）
    - size_mb: 文件大小（MB）
    """
    ensure_dirs()
    ext = os.path.splitext(file.filename)[1].lower()

    # 根据扩展名确定保存目录
    if ext in SUPPORTED_IMAGE_EXT:
        save_dir = UPLOADS_IMAGES_DIR
        dtype = "image"
    elif ext in SUPPORTED_VIDEO_EXT:
        save_dir = UPLOADS_VIDEOS_DIR
        dtype = "video"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    # 保存文件（添加随机前缀避免重名）
    filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = save_dir / filename
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "id": f"upload_{file_path.stem}",
        "name": file.filename,
        "path": str(file_path),
        "type": dtype,
        "size_mb": round(len(content) / (1024 * 1024), 2),
    }


# ====== 数据集管理 CRUD ======

class DatasetUpdate(BaseModel):
    """数据集更新请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None


@router.get("")
def list_datasets(db: Session = Depends(get_db)):
    """
    列出所有已管理的数据集

    返回：
    - List: 数据集列表，包含详细信息
    """
    datasets = dataset_service.get_datasets(db)
    return [
        {
            "id": ds.id,
            "name": ds.name,
            "description": ds.description,
            "path": ds.path,
            "file_size": ds.file_size,
            "image_count": ds.image_count,
            "label_count": ds.label_count,
            "class_names": ds.class_names,
            "class_distribution": ds.class_distribution,
            "created_at": str(ds.created_at) if ds.created_at else None,
        }
        for ds in datasets
    ]


@router.get("/{dataset_id}")
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """
    获取单个数据集详情

    参数：
    - dataset_id: 数据集 ID

    返回：
    - 数据集详细信息

    异常：
    - 404: 数据集不存在
    """
    ds = dataset_service.get_dataset(db, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {
        "id": ds.id,
        "name": ds.name,
        "description": ds.description,
        "path": ds.path,
        "file_size": ds.file_size,
        "image_count": ds.image_count,
        "label_count": ds.label_count,
        "class_names": ds.class_names,
        "class_distribution": ds.class_distribution,
        "created_at": str(ds.created_at) if ds.created_at else None,
    }


@router.post("/import")
async def import_dataset(
    file: UploadFile = File(...),      # ZIP 文件
    name: str = Form(...),             # 数据集名称
    description: str = Form(""),       # 数据集描述
    db: Session = Depends(get_db),     # 数据库会话
):
    """
    导入 YOLO 格式数据集

    支持的数据集结构：
    - 标准格式：images/ + labels/ 目录
    - 简单格式：图片和标注文件在同一目录
    - 子集格式：train/test/val 子目录

    自动分析内容：
    - 统计图片数量
    - 统计标注数量
    - 提取类别名称
    - 计算类别分布

    参数：
    - file: ZIP 格式的数据集包
    - name: 数据集名称
    - description: 数据集描述

    返回：
    - 数据集信息（包含分析结果）

    异常：
    - 400: 非 ZIP 格式
    - 500: 分析失败
    """
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="仅支持 ZIP 格式的数据集包")

    # 保存到临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 分析并创建数据集
        ds = dataset_service.create_dataset(db, name=name, description=description, zip_path=tmp_path)
        return {
            "id": ds.id,
            "name": ds.name,
            "description": ds.description,
            "image_count": ds.image_count,
            "label_count": ds.label_count,
            "class_names": ds.class_names,
            "class_distribution": ds.class_distribution,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据集分析失败: {str(e)}")
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.put("/{dataset_id}")
def update_dataset(dataset_id: int, update: DatasetUpdate, db: Session = Depends(get_db)):
    """
    更新数据集信息

    参数：
    - dataset_id: 数据集 ID
    - update: 更新数据（name、description）

    返回：
    - 更新后的数据集信息

    异常：
    - 404: 数据集不存在
    """
    ds = dataset_service.update_dataset(db, dataset_id, name=update.name, description=update.description)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"id": ds.id, "name": ds.name, "description": ds.description}


@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """
    删除数据集

    会同时删除：
    - 数据库记录
    - 数据集文件目录

    参数：
    - dataset_id: 数据集 ID

    返回：
    - dict: {"success": true}

    异常：
    - 404: 数据集不存在
    """
    success = dataset_service.delete_dataset(db, dataset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"success": True}


@router.get("/{dataset_id}/download")
def download_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """
    下载数据集（ZIP 格式）

    将数据集目录打包为 ZIP 文件下载

    参数：
    - dataset_id: 数据集 ID

    返回：
    - Response: ZIP 文件下载响应

    异常：
    - 404: 数据集或文件不存在
    """
    ds = dataset_service.get_dataset(db, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not os.path.exists(ds.path):
        raise HTTPException(status_code=404, detail="Dataset files not found")

    from fastapi.responses import Response
    zip_bytes = dataset_service.create_zip(ds.path)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{ds.name}.zip"'},
    )


@router.get("/{dataset_id}/splits")
def get_dataset_splits(dataset_id: int, db: Session = Depends(get_db)):
    """
    获取数据集子集信息

    检测数据集中的 train/test/val 子目录

    参数：
    - dataset_id: 数据集 ID

    返回：
    - List: 子集列表，每个包含 name 和 image_count

    示例返回：
    [
        {"name": "train", "image_count": 100},
        {"name": "val", "image_count": 20},
        {"name": "test", "image_count": 10}
    ]
    """
    ds = dataset_service.get_dataset(db, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    splits = dataset_service.detect_splits(ds.path)
    split_list = []
    for name in sorted(splits.keys()):
        images = dataset_service.get_split_images(ds.path, name)
        split_list.append({"name": name, "image_count": len(images)})

    # 如果没有检测到子集，返回默认的 "all"
    if not split_list:
        split_list.append({"name": "all", "image_count": ds.image_count})

    return split_list
