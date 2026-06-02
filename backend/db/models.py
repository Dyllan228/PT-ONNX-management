"""
数据库模型定义模块

本模块定义了系统中所有的数据库表结构，包括：
1. Model: 模型信息表（PT/ONNX 模型文件元数据）
2. Task: 异步任务表（转换、推理、性能测试任务）
3. BenchmarkRecord: 性能测试记录表
4. Dataset: 数据集信息表

使用 SQLAlchemy ORM 定义表结构，支持自动迁移和版本控制
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, BigInteger, Float, DateTime, JSON
from sqlalchemy.sql import func
from db.database import Base


class Model(Base):
    """
    模型信息表

    存储 PyTorch (.pt) 和 ONNX (.onnx) 模型的元数据信息
    支持同一模型的多个版本（通过 name + version 唯一标识）

    字段说明：
    - id: 自增主键
    - name: 模型名称（如 "yolov8n", "helmet-vest"）
    - version: 版本号（如 "v1", "v2.0"）
    - pt_file_path: PT 模型文件路径
    - onnx_file_path: ONNX 模型文件路径（转换后填充）
    - onnx_converted: 是否已转换为 ONNX 格式
    - description: 模型描述（自动生成或手动填写）
    - class_names: 类别名称列表（JSON 格式，如 ["helmet", "vest"]）
    - input_size: 输入尺寸（JSON 格式，如 [640, 640]）
    - param_count: 模型参数量
    - pt_file_size: PT 文件大小（字节）
    - onnx_file_size: ONNX 文件大小（字节）
    - training_epochs: 训练轮数
    - training_samples: 训练样本数
    - created_at: 创建时间（自动生成）
    """
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    version = Column(String(100), nullable=False)
    pt_file_path = Column(String(500), nullable=False)
    onnx_file_path = Column(String(500), nullable=True)
    onnx_converted = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    class_names = Column(JSON, nullable=True)
    input_size = Column(JSON, nullable=True)
    param_count = Column(BigInteger, nullable=True)
    pt_file_size = Column(BigInteger, nullable=True)
    onnx_file_size = Column(BigInteger, nullable=True)
    training_epochs = Column(Integer, nullable=True)
    training_samples = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class Task(Base):
    """
    异步任务表

    存储后台执行的异步任务状态，支持：
    - 模型转换任务（PT → ONNX）
    - 推理可视化任务（图片/视频推理）
    - 性能对比任务（速度、准确度测试）

    字段说明：
    - id: UUID 格式的任务 ID（36 位字符串）
    - type: 任务类型（convert/inference/benchmark）
    - status: 任务状态（pending/running/completed/failed）
    - progress: 进度百分比（0-100）
    - params: 任务参数（JSON 格式）
    - result: 任务结果（JSON 格式）
    - error_msg: 错误信息（失败时填充）
    - created_at: 创建时间
    - finished_at: 完成时间
    """
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True)
    type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    progress = Column(Integer, default=0)
    params = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error_msg = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    finished_at = Column(DateTime, nullable=True)


class BenchmarkRecord(Base):
    """
    性能测试记录表

    存储每次性能测试的详细结果，用于：
    - 历史记录查询
    - 性能趋势分析
    - 模型版本对比

    字段说明：
    - id: 自增主键
    - task_id: 关联的任务 ID
    - model_id: 关联的模型 ID
    - model_type: 模型类型（pt/onnx）
    - device: 测试设备（cpu/cuda）
    - avg_inference_ms: 平均推理耗时（毫秒）
    - avg_preprocess_ms: 平均预处理耗时（毫秒）
    - avg_postprocess_ms: 平均后处理耗时（毫秒）
    - peak_memory_mb: 峰值内存占用（MB）
    - model_size_mb: 模型文件大小（MB）
    - fps: 每秒处理帧数
    - precision_metrics: 精度指标（JSON 格式，包含 mAP、F1 等）
    - created_at: 创建时间
    """
    __tablename__ = "benchmark_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), nullable=False)
    model_id = Column(Integer, nullable=False)
    model_type = Column(String(10), nullable=False)
    device = Column(String(20), nullable=False)
    avg_inference_ms = Column(Float, nullable=True)
    avg_preprocess_ms = Column(Float, nullable=True)
    avg_postprocess_ms = Column(Float, nullable=True)
    peak_memory_mb = Column(Float, nullable=True)
    model_size_mb = Column(Float, nullable=True)
    fps = Column(Float, nullable=True)
    precision_metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class Dataset(Base):
    """
    数据集信息表

    存储导入的目标检测数据集元数据，支持：
    - YOLO 格式数据集（images/ + labels/ 目录结构）
    - 自动分析类别分布
    - 多子集管理（train/test/val）

    字段说明：
    - id: 自增主键
    - name: 数据集名称
    - description: 数据集描述
    - path: 数据集存储路径
    - file_size: 原始 ZIP 文件大小（字节）
    - image_count: 图片总数
    - label_count: 已标注图片数
    - class_names: 类别名称列表（JSON 格式）
    - class_distribution: 类别分布统计（JSON 格式，如 {"helmet": 150, "vest": 120}）
    - created_at: 创建时间
    """
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=True)
    image_count = Column(Integer, default=0)
    label_count = Column(Integer, default=0)
    class_names = Column(JSON, nullable=True)
    class_distribution = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
