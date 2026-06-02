from pydantic import BaseModel, ConfigDict
from typing import Optional


class InferenceRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_id: int
    model_type: str
    device: str
    dataset_id: Optional[int] = None
    confidence_threshold: Optional[float] = 0.5
