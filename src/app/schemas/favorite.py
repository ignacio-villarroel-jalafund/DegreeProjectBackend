from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
from app.schemas.recipe import ScrapedRecipeData

class FavoriteBase(BaseModel):
    recipe_id: uuid.UUID

class FavoriteCreate(FavoriteBase):
    pass

class FavoriteRecipeCreate(BaseModel):
    recipe_data: ScrapedRecipeData
    is_adapted: bool = False

class FavoriteUpdate(BaseModel):
    recipe_id: Optional[uuid.UUID] = None

class FavoriteInDBBase(FavoriteBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

class FavoriteRead(FavoriteInDBBase):
    pass

class FavoriteInDB(FavoriteInDBBase):
    pass
