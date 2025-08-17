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
        print("Starting `add_or_update_favorite`")
        recipe_to_favorite = None

        try:
            if not is_adapted and recipe_data.url:
                print(f"Searching recipe by URL: {recipe_data.url}")
                recipe_to_favorite = self.recipe_repo.get_by_url(db, url=str(recipe_data.url))
        except Exception as e:
            print(f"Error getting recipe by URL: {e}")

        if recipe_to_favorite is None:
            print("Recipe not found. Creating a new one.")
            try:
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
                print(f"Recipe created with ID: {recipe_to_favorite.id}")
            except Exception as e:
                print(f"Error creating recipe: {e}")
                raise

        try:
            print(f"Checking if recipe is already in user {user_id}'s favorites")
            existing_favorite = self.favorite_repo.get_by_user_and_recipe(
                db=db, user_id=user_id, recipe_id=recipe_to_favorite.id
            )
            if existing_favorite:
                print("Recipe already in favorites. Returning existing.")
                return existing_favorite
        except Exception as e:
            print(f"Error checking existing favorites: {e}")
            raise

        try:
            print("Adding recipe to favorites...")
            fav_schema = FavoriteCreate(recipe_id=recipe_to_favorite.id)
            fav_data = fav_schema.model_dump()
            fav_data['user_id'] = user_id

            db_obj = self.favorite_repo.model(**fav_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            print(f"Favorite added with ID: {db_obj.id}")
            return db_obj
        except Exception as e:
            print(f"Error adding favorite: {e}")
            db.rollback()
            raise

    def remove_favorite(self, db: Session, recipe_id: UUID, user_id: UUID) -> bool:
        print(f"--- Servicio: Intentando remover favorito (user: {user_id}, recipe: {recipe_id})")
        
        try:
            favorite = self.favorite_repo.get_by_user_and_recipe(
                db=db, user_id=user_id, recipe_id=recipe_id
            )
            
            if favorite:
                print(f"--- Servicio: Favorito encontrado (ID: {favorite.id}). Procediendo a eliminar.")
                
                deleted_in_repo = self.favorite_repo.delete_favorite(
                    db=db, user_id=user_id, recipe_id=recipe_id
                )

                if deleted_in_repo:
                    print("--- Servicio: El repositorio confirmó la eliminación.")
                    return True
                else:
                    print("--- Servicio: El repositorio no pudo eliminar el favorito, aunque fue encontrado.")
                    return False
            else:
                print("--- Servicio: No se encontró un favorito que coincida para eliminar.")
                return False
        except Exception as e:
            print(f"--- Servicio: Ocurrió un error al intentar eliminar el favorito: {e}")
            db.rollback()
            return False

    def get_favorites(self, db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Recipe]:
        print(f"Getting favorites for user {user_id} (skip={skip}, limit={limit})")
        try:
            favorites_assoc = self.favorite_repo.get_user_favorites(db=db, user_id=user_id, skip=skip, limit=limit)
            print(f"Retrieved {len(favorites_assoc)} favorites.")
            return [fav.recipe for fav in favorites_assoc]
        except Exception as e:
            print(f"Error getting favorites: {e}")
            return []


favorite_service = FavoriteService(favorite_repository, recipe_repository)
