from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.rating import Rating
from app.repositories.rating_repository import rating_repository
from app.repositories.recipe_repository import recipe_repository
from app.schemas.rating import RatingCreate, RatingUpdate


class RatingService:
    def __init__(self, rating_repo, recipe_repo):
        self.rating_repo = rating_repo
        self.recipe_repo = recipe_repo

    def rate_recipe(self, db: Session, rating_in: RatingCreate, recipe_id: str, user_id: str) -> Rating:
        recipe = self.recipe_repo.get(db, id=recipe_id)
        if not recipe:
            raise ValueError("Recipe not found")

        existing_rating = self.rating_repo.get_by_user_and_recipe(db=db, user_id=user_id, recipe_id=recipe_id)
        if existing_rating:
            raise ValueError("User has already rated this recipe")

        rating_data = rating_in.model_dump()
        rating_data["user_id"] = user_id
        rating_data["recipe_id"] = recipe_id
        return self.rating_repo.create(db=db, obj_in=RatingCreate(**rating_data))

    def get_rating(self, db: Session, rating_id: str) -> Optional[Rating]:
        return self.rating_repo.get(db=db, id=rating_id)

    def get_ratings_for_recipe(self, db: Session, recipe_id: str, skip: int = 0, limit: int = 100) -> List[Rating]:
        return self.rating_repo.get_ratings_by_recipe(db=db, recipe_id=recipe_id, skip=skip, limit=limit)

    def get_ratings_by_user(self, db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[Rating]:
        return self.rating_repo.get_ratings_by_user(db=db, user_id=user_id, skip=skip, limit=limit)

    def update_rating(self, db: Session, rating_id: str, rating_in: RatingUpdate) -> Optional[Rating]:
        db_rating = self.rating_repo.get(db=db, id=rating_id)
        if not db_rating:
            return None
        return self.rating_repo.update(db=db, db_obj=db_rating, obj_in=rating_in)

    def delete_rating(self, db: Session, rating_id: str) -> bool:
        deleted = self.rating_repo.remove(db=db, id=rating_id)
        return deleted is not None


rating_service = RatingService(rating_repository, recipe_repository)
