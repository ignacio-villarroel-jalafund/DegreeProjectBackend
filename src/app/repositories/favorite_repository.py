from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.favorite import Favorite
from app.schemas.favorite import FavoriteCreate, FavoriteUpdate
from app.repositories.base_repository import BaseRepository

class FavoriteRepository(BaseRepository[Favorite, FavoriteCreate, FavoriteUpdate]):
    
    def get_by_user_and_recipe(self, db: Session, *, user_id: int, recipe_id: int) -> Optional[Favorite]:
        return db.query(self.model).filter(self.model.user_id == user_id, self.model.recipe_id == recipe_id).first()

    def get_user_favorites(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[Favorite]:
        return db.query(self.model).filter(self.model.user_id == user_id)\
            .options(joinedload(self.model.recipe))\
            .offset(skip).limit(limit).all()

    def delete_favorite(self, db: Session, *, user_id: int, recipe_id: int) -> bool:
        favorite = self.get_by_user_and_recipe(db, user_id=user_id, recipe_id=recipe_id)
        if favorite:
            db.delete(favorite)
            db.commit()
            return True
        return False

favorite_repository = FavoriteRepository(Favorite)
