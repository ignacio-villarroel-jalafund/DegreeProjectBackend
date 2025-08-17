from pydantic import BaseModel
from typing import Optional, List
from .recipe import AdaptationRequest


class ShortRecipe(BaseModel):
    title: Optional[str] = None
    servings: Optional[int] = None
    ingredients: Optional[List[str]] = []
    directions: Optional[List[str]] = []


class ShortAdaptationRequest(BaseModel):
    recipe_data: ShortRecipe
    adaptation: AdaptationRequest
