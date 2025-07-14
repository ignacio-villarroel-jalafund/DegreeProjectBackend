from pydantic import BaseModel, Field, HttpUrl
from typing import Any, Dict, List, Literal, Optional
from datetime import datetime
import uuid

class RecipeSearchResult(BaseModel):
    title: str
    url: HttpUrl
    image_url: Optional[HttpUrl] = None

class RecipeBase(BaseModel):
    recipe_name: str
    servings: Optional[int] = None
    ingredients: str
    directions: str
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

class NutritionInfo(BaseModel):
    fat_total_g: float = Field(0.0, description="Grasas totales (g)")
    fat_saturated_g: float = Field(0.0, description="Grasas saturadas (g)")
    carbohydrates_total_g: float = Field(0.0, description="Carbohidratos totales (g)")
    fiber_g: float = Field(0.0, description="Fibra dietética (g)")
    sugar_g: float = Field(0.0, description="Azúcar (g)")
    sodium_mg: float = Field(0.0, description="Sodio (mg)")
    potassium_mg: float = Field(0.0, description="Potasio (mg)")
    cholesterol_mg: float = Field(0.0, description="Colesterol (mg)")
    source: str = Field("API Ninjas Nutrition", description="Fuente de los datos nutricionales")

class ScrapedRecipeData(BaseModel):
    title: Optional[str] = None
    image_url: Optional[str] = None
    servings: Optional[int] = None
    ingredients: Optional[List[str]] = []
    directions: Optional[List[str]] = []
    url: Optional[str] = None
    nutrition: Optional[NutritionInfo] = None

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

