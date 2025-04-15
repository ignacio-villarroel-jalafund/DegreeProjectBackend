from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.schemas.recipe import RecipeBase, RecipeCreate, RecipeRead
from app.services.recipe_service import recipe_service
from app.models.user import User as UserModel
from app.schemas.rating import RatingBase, RatingCreate
from app.services.rating_service import rating_service
from app.core.security import get_current_active_user

router = APIRouter()

@router.post("/", response_model=RecipeRead, status_code=status.HTTP_201_CREATED)
def create_recipe_endpoint(
    *,
    db: Session = Depends(get_db),
    recipe_in: RecipeCreate,
):
    recipe = recipe_service.create_recipe(db=db, recipe_in=recipe_in)
    return recipe

@router.get("/{recipe_id}", response_model=RecipeBase)
def read_recipe_endpoint(
    *,
    db: Session = Depends(get_db),
    recipe_id: UUID,
):
    db_recipe = recipe_service.repository.get(db, id=recipe_id)
    if db_recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return db_recipe

@router.post("/{recipe_id}/rate", response_model=RatingBase, status_code=status.HTTP_201_CREATED)
def rate_recipe_endpoint(
    *,
    db: Session = Depends(get_db),
    recipe_id: UUID,
    rating_in: RatingCreate,
    current_user: UserModel = Depends(get_current_active_user)
):
    try:
        rating = rating_service.rate_recipe(db, rating_in=rating_in, recipe_id=recipe_id, user_id=current_user.id)
        return rating
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif "already rated" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/", response_model=List[RecipeBase])
def list_recipes_endpoint(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    recipes = recipe_service.repository.get_multi(db, skip=skip, limit=limit)
    return recipes