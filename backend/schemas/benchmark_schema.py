from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class BenchmarkRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_ids: List[int]
    model_types: List[str]
    devices: List[str]
    dataset_id: Optional[int] = None
    dataset_path: Optional[str] = None
    dataset_split: Optional[str] = None
    confidence_threshold: Optional[float] = 0.5
    num_runs: Optional[int] = 100
    evaluate: Optional[bool] = False
