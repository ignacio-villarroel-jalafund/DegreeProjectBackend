from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
import uuid

class RatingBase(BaseModel):
    score: int = Field(ge=1, le=5)
    comment: Optional[str] = None

class RatingCreate(RatingBase):
    pass

class RatingUpdate(BaseModel):
    score: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = None

class RatingInDBBase(RatingBase):
    id: uuid.UUID
    user_id: uuid.UUID
    recipe_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class RatingRead(RatingInDBBase):
    pass

class RatingInDB(RatingInDBBase):
    pass
