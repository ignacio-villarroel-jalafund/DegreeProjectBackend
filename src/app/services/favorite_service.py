from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.models.favorite import Favorite
from app.models.recipe import Recipe
from app.repositories.favorite_repository import favorite_repository
from app.repositories.recipe_repository import recipe_repository
from app.schemas.favorite import FavoriteCreate
from app.schemas.recipe import ScrapedRecipeData, RecipeCreate


class FavoriteService:
    def __init__(self, favorite_repo, recipe_repo):
        self.favorite_repo = favorite_repo
        self.recipe_repo = recipe_repo

    def add_or_update_favorite(self, db: Session, user_id: UUID, recipe_data: ScrapedRecipeData, is_adapted: bool) -> Favorite:
        recipe_to_favorite = None

        if not is_adapted and recipe_data.url:
            recipe_to_favorite = self.recipe_repo.get_by_url(db, url=str(recipe_data.url))

        if recipe_to_favorite is None:
            create_data = RecipeCreate(
                recipe_name=recipe_data.title,
                servings=recipe_data.servings,
                ingredients="\n".join(recipe_data.ingredients) if recipe_data.ingredients else "",
                directions="\n".join(recipe_data.directions) if recipe_data.directions else "",
                url=str(recipe_data.url) if recipe_data.url else None,
                img_src=str(recipe_data.image_url) if recipe_data.image_url else None,
                nutrition=recipe_data.nutrition.model_dump_json() if recipe_data.nutrition else None,
                cuisine_path=None
            )
            recipe_to_favorite = self.recipe_repo.create(db=db, obj_in=create_data)

        existing_favorite = self.favorite_repo.get_by_user_and_recipe(
            db=db, user_id=user_id, recipe_id=recipe_to_favorite.id
        )

        if existing_favorite:
            return existing_favorite

        fav_schema = FavoriteCreate(recipe_id=recipe_to_favorite.id)
        fav_data = fav_schema.model_dump()
        fav_data['user_id'] = user_id
        
        db_obj = self.favorite_repo.model(**fav_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


    def remove_favorite(self, db: Session, recipe_id: UUID, user_id: UUID) -> bool:
        favorite = self.favorite_repo.get_by_user_and_recipe(db=db, user_id=user_id, recipe_id=recipe_id)
        if favorite:
            self.favorite_repo.remove(db=db, id=favorite.id)
            return True
        return False

    def get_favorites(self, db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Recipe]:
        favorites_assoc = self.favorite_repo.get_user_favorites(db=db, user_id=user_id, skip=skip, limit=limit)
        return [fav.recipe for fav in favorites_assoc]


favorite_service = FavoriteService(favorite_repository, recipe_repository)