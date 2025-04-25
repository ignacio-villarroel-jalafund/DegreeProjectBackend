from pydantic import BaseModel
from typing import Optional, Any

class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None

class TaskId(BaseModel):
    task_id: str