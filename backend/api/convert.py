"""
模型转换 API 模块

本模块提供 PyTorch 模型到 ONNX 格式的转换功能，包括：
1. 创建转换任务（异步执行）
2. 查询转换任务状态

路由前缀：/api/convert

技术说明：
- 使用 ThreadPoolExecutor 在后台线程执行转换
- 转换过程中实时更新进度到数据库
- 支持配置输入尺寸、ONNX Opset 版本、动态 Batch
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor
from db.database import get_db
from db.models import Task
from schemas.convert_schema import ConvertRequest
from services import model_service
from services.convert_service import convert_pt_to_onnx

# 创建路由器
router = APIRouter(prefix="/api/convert", tags=["convert"])

# 线程池执行器（最多 2 个并发转换任务）
executor = ThreadPoolExecutor(max_workers=2)


@router.post("")
def create_convert_task(req: ConvertRequest, db: Session = Depends(get_db)):
    """
    创建模型转换任务

    将 PyTorch (.pt) 模型转换为 ONNX (.onnx) 格式
    转换在后台线程异步执行，可通过返回的 task_id 查询进度

    请求体（ConvertRequest）：
    - model_id: 要转换的模型 ID
    - input_size: 输入尺寸，默认 [640, 640]
    - opset_version: ONNX Opset 版本，默认 11
    - dynamic_batch: 是否支持动态 Batch，默认 True

    返回：
    - task_id: 任务 ID（用于查询进度）
    - status: 初始状态（"pending"）

    异常：
    - 404: 模型不存在
    - 400: 模型已转换
    """
    # 验证模型是否存在
    model = model_service.get_model(db, req.model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if model.onnx_converted:
        raise HTTPException(status_code=400, detail="Model already converted to ONNX")

    # 创建任务记录
    task_id = uuid.uuid4().hex
    task = Task(
        id=task_id,
        type="convert",
        status="pending",
        params={
            "model_id": req.model_id,
            "input_size": req.input_size,
            "opset_version": req.opset_version,
            "dynamic_batch": req.dynamic_batch,
        },
    )
    db.add(task)
    db.commit()

    # 提交到线程池异步执行
    executor.submit(
        convert_pt_to_onnx,
        model_id=req.model_id,
        task_id=task_id,
        input_size=tuple(req.input_size),
        opset_version=req.opset_version,
        dynamic_batch=req.dynamic_batch,
    )

    return {"task_id": task_id, "status": "pending"}


@router.get("/{task_id}")
def get_convert_task(task_id: str, db: Session = Depends(get_db)):
    """
    查询转换任务状态

    参数：
    - task_id: 任务 ID

    返回：
    - task_id: 任务 ID
    - status: 任务状态（pending/running/completed/failed）
    - progress: 进度百分比（0-100）
    - result: 转换结果（包含 onnx_path）
    - error_msg: 错误信息（失败时）

    前端轮询建议：每 1-2 秒查询一次
    """
    task = db.query(Task).filter(Task.id == task_id, Task.type == "convert").first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": task.id,
        "status": task.status,
        "progress": task.progress,
        "result": task.result,
        "error_msg": task.error_msg,
    }
