from sqlalchemy.orm import Session
from typing import List

from app.models.favorite import Favorite
from app.models.recipe import Recipe
from app.repositories.favorite_repository import favorite_repository
from app.repositories.recipe_repository import recipe_repository
from app.schemas.favorite import FavoriteCreate


class FavoriteService:
    def __init__(self, favorite_repo, recipe_repo):
        self.favorite_repo = favorite_repo
        self.recipe_repo = recipe_repo

    def add_favorite(self, db: Session, recipe_id: str, user_id: str) -> Favorite:
        recipe = self.recipe_repo.get(db, id=recipe_id)
        if not recipe:
            raise ValueError("Recipe not found")

        existing_favorite = self.favorite_repo.get_by_user_and_recipe(db=db, user_id=user_id, recipe_id=recipe_id)
        if existing_favorite:
            return existing_favorite

        fav_data = FavoriteCreate(recipe_id=recipe_id)
        return self.favorite_repo.create_with_user(db=db, user_id=user_id, obj_in=fav_data)

    def remove_favorite(self, db: Session, recipe_id: str, user_id: str) -> bool:
        favorite = self.favorite_repo.get_by_user_and_recipe(db=db, user_id=user_id, recipe_id=recipe_id)
        if favorite:
            self.favorite_repo.remove(db=db, id=favorite.id)
            return True
        return False

    def get_favorites(self, db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[Recipe]:
        favorites_assoc = self.favorite_repo.get_user_favorites(db=db, user_id=user_id, skip=skip, limit=limit)
        return [fav.recipe for fav in favorites_assoc]


favorite_service = FavoriteService(favorite_repository, recipe_repository)
