from pydantic import BaseModel
from typing import Optional
import uuid

class DietBase(BaseModel):
    name: str
    description: Optional[str] = None

class DietCreate(DietBase):
    pass

class DietUpdate(DietBase):
    pass

class DietRead(DietBase):
    id: uuid.UUID

    class Config:
        from_attributes = True