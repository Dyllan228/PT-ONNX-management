"""
性能对比 API 模块

本模块提供模型性能对比功能，包括：
1. 速度测试（推理耗时、FPS）
2. 资源占用（内存、模型大小）
3. 准确度评估（精确率、召回率、F1、mAP）

支持的对比模式：
- PT vs ONNX：同一模型的两种格式对比
- PT vs PT：不同版本 PT 模型对比
- ONNX vs ONNX：不同版本 ONNX 模型对比

路由前缀：/api/benchmark
"""

import os
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor
from db.database import get_db
from db.models import Task
from schemas.benchmark_schema import BenchmarkRequest
from services import model_service, dataset_service
from services.benchmark_service import run_benchmark
from storage.file_manager import BASE_DIR

# 创建路由器
router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])

# 线程池执行器（最多 2 个并发测试任务）
executor = ThreadPoolExecutor(max_workers=2)


@router.post("")
def create_benchmark_task(req: BenchmarkRequest, db: Session = Depends(get_db)):
    """
    创建性能对比任务

    请求体（BenchmarkRequest）：
    - model_ids: 模型 ID 列表
    - model_types: 对应的模型类型列表（pt/onnx）
    - devices: 测试设备列表（cpu/cuda）
    - dataset_id: 数据集 ID（可选）
    - dataset_path: 数据集路径（可选，与 dataset_id 二选一）
    - dataset_split: 数据集子集（train/test/val）
    - confidence_threshold: 置信度阈值
    - num_runs: 测试次数（默认 100）
    - evaluate: 是否评估准确度（需要数据集包含标注）

    返回：
    - task_id: 任务 ID
    - status: 初始状态（"pending"）

    异常：
    - 404: 模型不存在
    """
    # 验证所有模型是否存在
    for model_id in req.model_ids:
        model = model_service.get_model(db, model_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    # 创建任务记录
    task_id = uuid.uuid4().hex
    task = Task(
        id=task_id,
        type="benchmark",
        status="pending",
        params=req.model_dump(),
    )
    db.add(task)
    db.commit()

    # 获取输入尺寸（使用第一个模型的配置）
    first_model = model_service.get_model(db, req.model_ids[0])
    input_size = tuple(first_model.input_size) if first_model and first_model.input_size else (640, 640)

    # 确定数据源
    dataset_path = None
    if req.dataset_id:
        ds = dataset_service.get_dataset(db, req.dataset_id)
        if ds:
            dataset_path = ds.path
    elif req.dataset_path and os.path.exists(req.dataset_path):
        dataset_path = req.dataset_path

    # 提交到线程池异步执行
    executor.submit(
        run_benchmark,
        task_id=task_id,
        model_ids=req.model_ids,
        model_types=req.model_types,
        devices=req.devices,
        data_path=dataset_path,
        dataset_split=req.dataset_split,
        input_size=input_size,
        conf_threshold=req.confidence_threshold,
        num_runs=req.num_runs or 100,
        evaluate=req.evaluate or False,
    )

    return {"task_id": task_id, "status": "pending"}


@router.get("/{task_id}")
def get_benchmark_task(task_id: str, db: Session = Depends(get_db)):
    """
    查询性能对比任务状态

    参数：
    - task_id: 任务 ID

    返回：
    - task_id: 任务 ID
    - status: 任务状态（pending/running/completed/failed）
    - progress: 进度百分比（0-100）
    - result: 测试结果（包含 benchmarks 数组）
    - error_msg: 错误信息

    result.benchmarks 数组结构：
    [
        {
            "model_id": 模型ID,
            "model_name": 模型名称,
            "model_version": 版本,
            "model_type": "pt"/"onnx",
            "device": "cpu"/"cuda",
            "avg_inference_ms": 平均推理耗时,
            "avg_preprocess_ms": 平均预处理耗时,
            "avg_postprocess_ms": 平均后处理耗时,
            "fps": 每秒帧数,
            "peak_memory_mb": 峰值内存,
            "model_size_mb": 模型大小,
            "precision": 精确率（可选）,
            "recall": 召回率（可选）,
            "f1": F1分数（可选）,
            "mAP": mAP@0.5（可选）
        }
    ]
    """
    task = db.query(Task).filter(Task.id == task_id, Task.type == "benchmark").first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": task.id,
        "status": task.status,
        "progress": task.progress,
        "result": task.result,
        "error_msg": task.error_msg,
    }
