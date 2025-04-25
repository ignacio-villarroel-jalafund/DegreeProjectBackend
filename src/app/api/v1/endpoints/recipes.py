from typing import List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import HttpUrl
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.schemas.recipe import RecipeBase, RecipeSearchResult, ScrapeRequest, ScrapedRecipeData
from app.schemas.task import TaskId
from app.services.search_service import search_service
from app.services.recipe_service import recipe_service
from app.models.user import User as UserModel
from app.schemas.rating import RatingBase, RatingCreate
from app.services.rating_service import rating_service
from app.core.security import get_current_active_user
from app.tasks.recipe_tasks import scrape_url_data, analyze_and_return

router = APIRouter()

@router.get("/search", response_model=List[RecipeSearchResult])
def search_recipes_endpoint(
    query: str = Query(..., min_length=3, description="Search term for recipes")
):
    if not query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Search term cannot be empty.")
    results = search_service.search_recipes(query)
    if not results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No recipes found for that search.")
    return results

@router.post("/scrape", response_model=ScrapedRecipeData, status_code=status.HTTP_200_OK)
async def scrape_recipe_url_endpoint(
    scrape_request: ScrapeRequest = Body(...)
):
    url = str(scrape_request.url)
    print(f"Received request to SCRAPE URL: {url}")
    try:
        scraped_data = await scrape_url_data(url)
        return ScrapedRecipeData(**scraped_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        print(f"Unexpected error in /scrape endpoint: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error processing the scraping request.")

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
