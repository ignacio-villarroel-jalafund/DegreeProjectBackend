import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

from app.schemas.recipe import ScrapedRecipeData

class HistoryBase(BaseModel):
    recipe_data: Dict[str, Any]
    source_url: Optional[str] = None
    is_adapted: bool = False

class HistoryCreate(HistoryBase):
    user_id: uuid.UUID

class HistoryUpdate(HistoryBase):
    pass

class HistoryRead(BaseModel):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    recipe_data: ScrapedRecipeData
    source_url: Optional[str] = None
    is_adapted: bool

    class Config:
        from_attributes = True