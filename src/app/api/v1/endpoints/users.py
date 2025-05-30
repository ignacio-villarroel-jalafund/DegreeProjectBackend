from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated, List, Any
from uuid import UUID

from app.core.database import get_db
from app.schemas.favorite import FavoriteBase as FavoriteSchema
from app.schemas.recipe import RecipeBase as RecipeSchema
from app.schemas.user import User, UserCreate

from app.services.favorite_service import favorite_service
from app.services.user_service import user_service
from app.core.security import (
    get_current_active_user,
    create_access_token,
    authenticate_user
)
from app.models.user import User as UserModel

router = APIRouter()

@router.post("/token")
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
) -> Any:
    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate
):
    db_user = user_service.repository.get_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered.",
        )
    user = user_service.create_user(db=db, user_in=user_in)
    return user

@router.get("/me", response_model=User)
def read_users_me(
    current_user: UserModel = Depends(get_current_active_user)
):
    return current_user

@router.post("/me/favorites/{recipe_id}", response_model=FavoriteSchema, status_code=status.HTTP_201_CREATED)
def add_favorite_recipe_endpoint(
    *,
    db: Session = Depends(get_db),
    recipe_id: UUID,
    current_user: UserModel = Depends(get_current_active_user)
):
    try:
        favorite_model = favorite_service.add_favorite(db, recipe_id=recipe_id, user_id=current_user.id)
        return favorite_model
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif "already favorite" in str(e).lower():
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/me/favorites/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite_recipe_endpoint(
    *,
    db: Session = Depends(get_db),
    recipe_id: UUID,
    current_user: UserModel = Depends(get_current_active_user)
):
    deleted = favorite_service.remove_favorite(db, recipe_id=recipe_id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Favorite not found for this user and recipe")

@router.get("/me/favorites", response_model=List[RecipeSchema])
def get_favorite_recipes_endpoint(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_active_user)
):
    recipes = favorite_service.get_favorites(db, user_id=current_user.id, skip=skip, limit=limit)
    return recipes
