from typing import Optional
from app.models.recipe import Recipe
from app.schemas.recipe import RecipeCreate, RecipeUpdate
from app.repositories.base_repository import BaseRepository
from sqlalchemy.orm import Session

class RecipeRepository(BaseRepository[Recipe, RecipeCreate, RecipeUpdate]):
    def get_by_url(self, db: Session, *, url: str) -> Optional[Recipe]:
        return self.get_by_attribute(db, attribute="url", value=url)
    
recipe_repository = RecipeRepository(Recipe)
