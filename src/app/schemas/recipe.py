from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class RecipeBase(BaseModel):
    recipe_name: str
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    total_time: Optional[int] = None
    servings: Optional[int] = None
    yield_amount: Optional[str] = None
    ingredients: str
    directions: str
    rating: Optional[float] = None
    url: Optional[str] = None
    cuisine_path: Optional[str] = None
    nutrition: Optional[str] = None
    timing: Optional[str] = None
    img_src: Optional[str] = None

class RecipeCreate(RecipeBase):
    pass

class RecipeUpdate(BaseModel):
    recipe_name: Optional[str] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    total_time: Optional[int] = None
    servings: Optional[int] = None
    yield_amount: Optional[str] = None
    ingredients: Optional[str] = None
    directions: Optional[str] = None
    rating: Optional[float] = None
    url: Optional[str] = None
    cuisine_path: Optional[str] = None
    nutrition: Optional[str] = None
    timing: Optional[str] = None
    img_src: Optional[str] = None

class RecipeInDBBase(RecipeBase):   
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class RecipeRead(RecipeInDBBase):
    pass

class RecipeInDB(RecipeInDBBase):
    pass
