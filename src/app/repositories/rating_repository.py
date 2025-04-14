from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.rating import Rating
from app.schemas.rating import RatingCreate, RatingUpdate
from app.repositories.base_repository import BaseRepository

class RatingRepository(BaseRepository[Rating, RatingCreate, RatingUpdate]):
    
    def get_by_user_and_recipe(self, db: Session, *, user_id: int, recipe_id: int) -> Optional[Rating]:
        return db.query(self.model).filter(self.model.user_id == user_id, self.model.recipe_id == recipe_id).first()

    def get_ratings_by_recipe(self, db: Session, *, recipe_id: int, skip: int = 0, limit: int = 100) -> List[Rating]:
        return db.query(self.model).filter(self.model.recipe_id == recipe_id).offset(skip).limit(limit).all()

    def get_ratings_by_user(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[Rating]:
        return db.query(self.model).filter(self.model.user_id == user_id).offset(skip).limit(limit).all()

rating_repository = RatingRepository(Rating)
