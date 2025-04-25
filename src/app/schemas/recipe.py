from pydantic import BaseModel, HttpUrl
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

class RecipeSearchResult(BaseModel):
    title: str
    url: HttpUrl

class RecipeBase(BaseModel):
    recipe_name: str
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    total_time: Optional[int] = None
    servings: Optional[int] = None
    ingredients: str
    directions: str
    rating: Optional[float] = None
    url: HttpUrl = None
    cuisine_path: Optional[str] = None
    nutrition: Optional[str] = None
    img_src: Optional[HttpUrl] = None

class RecipeCreate(RecipeBase):
    url: HttpUrl
    recipe_name: str
    pass

class RecipeUpdate(RecipeBase):
    recipe_name: Optional[str] = None
    url: Optional[HttpUrl] = None

class ScrapeRequest(BaseModel):
    url: HttpUrl

class ScrapedRecipeData(BaseModel):
    recipe_name: Optional[str] = None
    ingredients: Optional[List[str]] = None
    directions: Optional[List[str]] = None

class RecipeRead(RecipeBase):   
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

