from sqlalchemy.orm import Session
from typing import Optional, List
from app.repositories.user_repository import user_repository
from app.schemas.user import UserCreate, UserUpdate, UserUpdatePassword, UserUpdateDetails
from app.models.user import User
from app.core.security import get_password_hash, verify_password

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
        
        if self.repository.get_by_username(db=db, username=user_in.username): #
            raise ValueError("Username already registered")

        user_data = user_in.model_dump()
        user_data["password"] = get_password_hash(user_in.password) #

        return self.repository.create(db=db, obj_in=UserCreate(**user_data))

    def update_user(self, db: Session, user_id: int, user_in: UserUpdate) -> Optional[User]:
        user = self.repository.get(db=db, id=user_id)
        if not user:
            return None
        return self.repository.update(db=db, db_obj=user, obj_in=user_in) #

    def update_user_details(self, db: Session, db_user: User, user_in: UserUpdateDetails) -> User:
        if user_in.email and user_in.email != db_user.email:
            existing_user = self.repository.get_by_email(db, email=user_in.email)
            if existing_user and existing_user.id != db_user.id:
                raise ValueError("Email already registered by another user.")
        
        if user_in.username and user_in.username != db_user.username:
            existing_user = self.repository.get_by_username(db, username=user_in.username) #
            if existing_user and existing_user.id != db_user.id:
                raise ValueError("Username already taken by another user.")

        update_data = user_in.model_dump(exclude_unset=True)
        return self.repository.update(db=db, db_obj=db_user, obj_in=update_data) #

    def update_user_password(self, db: Session, db_user: User, password_in: UserUpdatePassword) -> bool:
        if not verify_password(password_in.current_password, db_user.password): #
            return False
        if password_in.new_password != password_in.confirm_password:
            raise ValueError("New password and confirmation password do not match.")
        
        hashed_password = get_password_hash(password_in.new_password) #
        update_data = {"password": hashed_password}
        self.repository.update(db=db, db_obj=db_user, obj_in=update_data) #
        return True

    def delete_user(self, db: Session, user_id: int) -> Optional[User]:
        return self.repository.remove(db=db, id=user_id)

user_service = UserService(user_repository)
