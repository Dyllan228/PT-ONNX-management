from pydantic import BaseModel
from typing import Optional, List


class ConvertRequest(BaseModel):
    model_id: int
    input_size: Optional[List[int]] = [640, 640]
    dynamic_batch: Optional[bool] = True
    opset_version: Optional[int] = 11
