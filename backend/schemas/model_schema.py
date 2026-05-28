from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ModelCreate(BaseModel):
    name: str
    version: str
    pt_file_path: str
    class_names: Optional[List[str]] = None
    input_size: Optional[List[int]] = None
    training_epochs: Optional[int] = None
    training_samples: Optional[int] = None


class ModelUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    class_names: Optional[List[str]] = None
    input_size: Optional[List[int]] = None
    training_epochs: Optional[int] = None
    training_samples: Optional[int] = None


class ModelResponse(BaseModel):
    id: int
    name: str
    version: str
    pt_file_path: str
    onnx_file_path: Optional[str] = None
    onnx_converted: bool
    description: Optional[str] = None
    class_names: Optional[List[str]] = None
    input_size: Optional[List[int]] = None
    param_count: Optional[int] = None
    pt_file_size: Optional[int] = None
    onnx_file_size: Optional[int] = None
    training_epochs: Optional[int] = None
    training_samples: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
