from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.recipe import Recipe
from app.repositories.recipe_repository import recipe_repository
from app.schemas.recipe import RecipeCreate, RecipeUpdate


class RecipeService:
    def __init__(self, repository):
        self.repository = repository

    def create_recipe(self, db: Session, recipe_in: RecipeCreate) -> Recipe:
        recipe_data = recipe_in.model_dump()
        return self.repository.create(db=db, obj_in=RecipeCreate(**recipe_data))

    def get_recipe(self, db: Session, recipe_id: int) -> Optional[Recipe]:
        return self.repository.get(db=db, id=recipe_id)

    def get_all_recipes(self, db: Session, skip: int = 0, limit: int = 10) -> List[Recipe]:
        return self.repository.get_multi(db=db, skip=skip, limit=limit)

    def update_recipe(self, db: Session, recipe_id: int, recipe_in: RecipeUpdate) -> Optional[Recipe]:
        db_recipe = self.repository.get(db=db, id=recipe_id)
        if not db_recipe:
            return None
        return self.repository.update(db=db, db_obj=db_recipe, obj_in=recipe_in)

    def delete_recipe(self, db: Session, recipe_id: int) -> bool:
        deleted = self.repository.remove(db=db, id=recipe_id)
        return deleted is not None


recipe_service = RecipeService(recipe_repository)
