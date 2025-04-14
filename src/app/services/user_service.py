from sqlalchemy.orm import Session
from typing import Optional, List
from app.repositories.user_repository import user_repository
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User
from app.core.security import get_password_hash

class UserService:
    def __init__(self, repository):
        self.repository = repository

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        return self.repository.get_by_email(db=db, email=email)

    def get_user(self, db: Session, user_id: int) -> Optional[User]:
        return self.repository.get(db=db, id=user_id)

    def get_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        return self.repository.get_multi(db=db, skip=skip, limit=limit)

    def create_user(self, db: Session, user_in: UserCreate) -> User:
        if self.repository.get_by_email(db=db, email=user_in.email):
            raise ValueError("Email already registered")

        user_data = user_in.model_dump()
        user_data["password"] = get_password_hash(user_in.password)

        return self.repository.create(db=db, obj_in=UserCreate(**user_data))

    def update_user(self, db: Session, user_id: int, user_in: UserUpdate) -> Optional[User]:
        user = self.repository.get(db=db, id=user_id)
        if not user:
            return None

        return self.repository.update(db=db, db_obj=user, obj_in=user_in)

    def delete_user(self, db: Session, user_id: int) -> Optional[User]:
        return self.repository.remove(db=db, id=user_id)

user_service = UserService(user_repository)
