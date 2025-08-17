from pydantic import BaseModel
from typing import Optional
import uuid

class AllergyBase(BaseModel):
    name: str
    description: Optional[str] = None

class AllergyCreate(AllergyBase):
    pass

class AllergyUpdate(AllergyBase):
    pass

class AllergyRead(AllergyBase):
    id: uuid.UUID

    class Config:
        from_attributes = True