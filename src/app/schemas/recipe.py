from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Any, Dict, List, Literal, Optional
from datetime import datetime
import uuid

class RecipeSearchResult(BaseModel):
    title: str
    url: HttpUrl
    image_url: Optional[HttpUrl] = None

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

class RecipeTime(BaseModel):
    cookTime: Optional[int] = None
    prepTime: Optional[int] = None
    totalTime: Optional[int] = None

    @field_validator('cookTime', 'prepTime', 'totalTime', mode='before')
    @classmethod
    def parse_null_string_as_none(cls, value: Any) -> Optional[int]:
        if isinstance(value, str) and value.lower() == 'null':
            return None
        return value

class ScrapedRecipeData(BaseModel):
    title: Optional[str] = None
    image_url: Optional[str] = None
    servings: Optional[int] = None
    time: Optional[RecipeTime] = None 
    ingredients: Optional[List[str]] = []
    directions: Optional[List[str]] = []
    url: Optional[str] = None

class RecipeRead(RecipeBase):   
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

AnalysisType = Literal[
    "SUBSTITUTE_INGREDIENT", 
    "ADAPT_DIET", 
    "SCALE_PORTIONS"
]

class AdaptationRequest(BaseModel):
    type: AnalysisType = Field(..., description="The type of analysis to perform.")
    details: Dict[str, Any] = Field(..., description="Specific details for the action, e.g., {'from': 'ing1', 'to': 'gluten-free'}")

class RecipeAdaptationRequest(BaseModel):
    recipe_data: ScrapedRecipeData = Field(..., description="The complete data of the current recipe.")
    adaptation: AdaptationRequest = Field(..., description="The desired adaptation instruction.")

class RecipeAdaptationResponse(BaseModel):
    updated_recipe: ScrapedRecipeData = Field(..., description="The complete recipe with the applied modifications.")

class NutritionInfo(BaseModel):
    calories: Optional[float] = Field(None, description="Calorías totales aproximadas (kcal).")
    protein: Optional[float] = Field(None, description="Proteínas totales aproximadas (g).")
    carbohydrates: Optional[float] = Field(None, description="Carbohidratos totales aproximados (g).")
    fat: Optional[float] = Field(None, description="Grasas totales aproximadas (g).")
    source: str = "Open Food Facts (Estimación sumando valores por 100g de cada ingrediente)"

class ScrapedRecipeData(BaseModel):
    title: Optional[str] = None
    image_url: Optional[str] = None
    servings: Optional[int] = None
    time: Optional[RecipeTime] = None 
    ingredients: Optional[List[str]] = []
    directions: Optional[List[str]] = []
    url: Optional[str] = None
    nutrition: Optional[NutritionInfo] = None
