from sqlalchemy import Column, Integer, String, Text, Boolean, BigInteger, Float, DateTime, JSON
from sqlalchemy.sql import func
from db.database import Base


class Model(Base):
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
