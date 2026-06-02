from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class ConvertRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_id: int
    input_size: Optional[List[int]] = [640, 640]
    dynamic_batch: Optional[bool] = True
    opset_version: Optional[int] = 11
