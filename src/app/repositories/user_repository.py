from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(self.model).filter(self.model.email == email).first()

user_repository = UserRepository(User)
