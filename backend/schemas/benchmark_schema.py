from pydantic import BaseModel
from typing import Optional, List


class BenchmarkRequest(BaseModel):
    model_ids: List[int]
    model_types: List[str]
    devices: List[str]
    dataset_id: Optional[int] = None
    confidence_threshold: Optional[float] = 0.5
    num_runs: Optional[int] = 100
