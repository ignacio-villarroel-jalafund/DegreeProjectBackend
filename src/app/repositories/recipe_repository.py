from app.models.recipe import Recipe
from app.schemas.recipe import RecipeCreate, RecipeUpdate
from app.repositories.base_repository import BaseRepository

class RecipeRepository(BaseRepository[Recipe, RecipeCreate, RecipeUpdate]):
    pass

recipe_repository = RecipeRepository(Recipe)
