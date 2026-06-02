"""
推理可视化 API 模块

本模块提供模型推理功能，支持：
1. 图片推理（单张图片或数据集目录）
2. 视频推理（逐帧处理并生成结果视频）
3. 实时进度查询
4. 结果图片/视频下载

路由前缀：/api/inference

技术特点：
- 异步执行：推理在后台线程运行
- 逐帧保存：每帧结果独立保存，支持实时预览
- 可终止：支持中途取消推理任务
"""

import uuid
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor
from db.database import get_db
from db.models import Task
from services import model_service
from services.inference_service import run_inference, cancel_inference
from storage.file_manager import UPLOADS_IMAGES_DIR, UPLOADS_VIDEOS_DIR, RESULTS_DIR, ensure_dirs

# 创建路由器
router = APIRouter(prefix="/api/inference", tags=["inference"])

# 线程池执行器（最多 2 个并发推理任务）
executor = ThreadPoolExecutor(max_workers=2)


@router.post("")
async def create_inference_task(
    mid: int = Form(...),                      # 模型 ID
    mtype: str = Form(...),                     # 模型类型（pt/onnx）
    device: str = Form("cpu"),                  # 推理设备（cpu/cuda）
    confidence_threshold: float = Form(0.5),    # 置信度阈值
    dataset_path: str = Form(None),             # 数据集路径
    file: UploadFile = File(None),              # 上传的文件
    db: Session = Depends(get_db),              # 数据库会话
):
    """
    创建推理任务

    支持三种数据源：
    1. 上传文件（图片或视频）
    2. 指定数据集路径
    3. 指定单个文件路径

    表单参数：
    - mid: 模型 ID
    - mtype: 模型类型（"pt" 或 "onnx"）
    - device: 推理设备（"cpu" 或 "cuda"）
    - confidence_threshold: 置信度阈值（0-1，默认 0.5）
    - dataset_path: 数据集目录或文件路径
    - file: 上传的图片/视频文件

    返回：
    - task_id: 任务 ID（用于查询进度和获取结果）
    - status: 初始状态（"pending"）

    异常：
    - 400: 不支持的文件类型或数据源不存在
    - 404: 模型不存在
    """
    model_id = mid
    model_type = mtype

    # 验证模型
    model = model_service.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if model_type == "onnx" and not model.onnx_converted:
        raise HTTPException(status_code=400, detail="Model not yet converted to ONNX")

    # 处理数据源
    if file:
        # 情况1：上传的文件
        ensure_dirs()
        ext = os.path.splitext(file.filename)[1].lower()
        if ext in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
            save_dir = UPLOADS_IMAGES_DIR
        elif ext in {".mp4", ".avi", ".mov", ".mkv"}:
            save_dir = UPLOADS_VIDEOS_DIR
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # 保存文件（添加随机前缀避免重名）
        filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
        file_path = save_dir / filename
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        data_path = str(file_path)
    elif dataset_path:
        # 情况2：指定的数据集路径
        if not os.path.exists(dataset_path):
            raise HTTPException(status_code=400, detail=f"Dataset file not found: {dataset_path}")
        data_path = dataset_path
    else:
        raise HTTPException(status_code=400, detail="No data source provided")

    # 创建任务记录
    task_id = uuid.uuid4().hex
    task = Task(
        id=task_id,
        type="inference",
        status="pending",
        params={
            "model_id": model_id,
            "model_type": model_type,
            "device": device,
            "confidence_threshold": confidence_threshold,
            "data_path": data_path,
        },
    )
    db.add(task)
    db.commit()

    # 提交到线程池异步执行
    input_size = tuple(model.input_size) if model.input_size else (640, 640)
    executor.submit(
        run_inference,
        model_id=model_id,
        task_id=task_id,
        model_type=model_type,
        device=device,
        data_path=data_path,
        input_size=input_size,
        conf_threshold=confidence_threshold,
    )

    return {"task_id": task_id, "status": "pending"}


@router.get("/{task_id}")
def get_inference_task(task_id: str, db: Session = Depends(get_db)):
    """
    查询推理任务状态

    参数：
    - task_id: 任务 ID

    返回：
    - task_id: 任务 ID
    - status: 任务状态（pending/running/completed/failed）
    - progress: 进度百分比（0-100）
    - result: 推理结果（包含 detections_summary、total_frames 等）
    - error_msg: 错误信息

    result 字段结构：
    {
        "annotated_dir": "标注结果目录",
        "total_frames": 已处理帧数,
        "detections_summary": [每帧的检测结果],
        "device": "推理设备",
        "model_type": "模型类型",
        "video_path": "结果视频路径（仅视频推理）"
    }
    """
    task = db.query(Task).filter(Task.id == task_id, Task.type == "inference").first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": task.id,
        "status": task.status,
        "progress": task.progress,
        "result": task.result,
        "error_msg": task.error_msg,
    }


@router.get("/{task_id}/image/{frame_idx}")
def get_result_image(task_id: str, frame_idx: int):
    """
    获取推理结果图片

    用于实时预览推理结果，前端通过轮询加载新帧

    参数：
    - task_id: 任务 ID
    - frame_idx: 帧序号（从 0 开始）

    返回：
    - FileResponse: JPEG 格式的标注结果图片

    文件命名规则：
    - 视频/数据集推理：frame_000000.jpg, frame_000001.jpg, ...
    - 单张图片推理：frame_000000.jpg 或 result.jpg
    """
    from fastapi.responses import FileResponse

    # 尝试按帧序号查找
    img_path = RESULTS_DIR / task_id / "annotated" / f"frame_{frame_idx:06d}.jpg"
    if not img_path.exists():
        # 回退到通用结果图片
        img_path = RESULTS_DIR / task_id / "annotated" / "result.jpg"
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Result image not found")
    return FileResponse(str(img_path))


@router.get("/{task_id}/video")
def get_result_video(task_id: str):
    """
    获取推理结果视频

    仅视频推理任务会生成结果视频

    参数：
    - task_id: 任务 ID

    返回：
    - FileResponse: MP4 格式的结果视频

    异常：
    - 404: 视频文件不存在
    """
    from fastapi.responses import FileResponse

    video_path = RESULTS_DIR / task_id / "annotated" / "result.mp4"
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Result video not found")
    return FileResponse(str(video_path), media_type="video/mp4", filename="result.mp4")


@router.delete("/{task_id}")
def cancel_inference_task(task_id: str, db: Session = Depends(get_db)):
    """
    取消推理任务

    发送取消信号，推理会在当前帧处理完成后停止

    参数：
    - task_id: 任务 ID

    返回：
    - success: 是否成功发送取消信号
    - message: 提示信息

    异常：
    - 400: 任务已完成或失败
    - 404: 任务不存在
    """
    task = db.query(Task).filter(Task.id == task_id, Task.type == "inference").first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status in ("completed", "failed"):
        raise HTTPException(status_code=400, detail="Task already finished")
    cancel_inference(task_id)
    return {"success": True, "message": "取消信号已发送"}
