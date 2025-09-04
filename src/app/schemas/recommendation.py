from pydantic import BaseModel
from app.schemas.recipe import RecipeRead

class Recommendation(BaseModel):
    reason: str
    recipe: RecipeRead

    class Config:
        from_attributes = True
