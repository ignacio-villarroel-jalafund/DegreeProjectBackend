from typing import List
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.schemas.ingredient import IngredientInfoResponse
from app.schemas.recipe import RecipeBase, RecipeSearchResult, ScrapeRequest, ScrapedRecipeData, RecipeAdaptationRequest, RecipeAdaptationResponse
from app.schemas.task import TaskId
from app.services import nutrition_service
from app.services.search_service import search_service
from app.services.recipe_service import recipe_service
from app.models.user import User
from app.tasks.recipe_tasks import scrape_and_analyze_recipe
from app.services.ai_agents_service import ai_agents_service

router = APIRouter()

@router.get("/search", response_model=List[RecipeSearchResult])
def search_recipes_endpoint(
    query: str = Query(..., min_length=3,
                       description="Search term for recipes")
):
    if not query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Search term cannot be empty.")
    results = search_service.search_recipes(query)
    if not results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="No recipes found for that search.")
    return results

@router.get("/ingredient-info", response_model=IngredientInfoResponse)
def get_ingredient_information_endpoint(
    text_query: str = Query(..., min_length=1, description="Text to extract ingredient from and get info")
):
    if not text_query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text query cannot be empty."
        )

    try:
        ingredient_data_dict = search_service.get_ingredient(text_query)

        if ingredient_data_dict is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Could not extract or find information for the ingredient from the provided text."
            )
        
        return IngredientInfoResponse(**ingredient_data_dict)

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected error in /ingredient-info endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.post("/scrape", response_model=ScrapedRecipeData, status_code=status.HTTP_200_OK)
async def scrape_recipe_url_endpoint(
    scrape_request: ScrapeRequest = Body(...)
):
    url = str(scrape_request.url)
    print(f"Received request to SCRAPE URL: {url}")
    try:
        scraped_data = await scrape_and_analyze_recipe(url)
        return ScrapedRecipeData(**scraped_data) if isinstance(scraped_data, dict) else scraped_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        print(f"Unexpected error in /scrape endpoint: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal error processing scraping request.")


@router.post("/analyze", response_model=TaskId, status_code=status.HTTP_202_ACCEPTED)
async def analyze_scraped_recipe_endpoint(
    scraped_data: ScrapedRecipeData = Body(...)
):
    print(f"Received request to ANALYZE recipe: {scraped_data.recipe_name}")

    try:
        scraped_data_dict = scraped_data.model_dump(mode='json')

        task = scrape_and_analyze_recipe.delay(scraped_data_dict)
        print(f"Analysis Celery task started with ID: {task.id}")
        return TaskId(task_id=task.id)
    except Exception as e:
        print(f"Error sending analysis task to Celery: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not start recipe analysis: {e}"
        )


@router.get("/{recipe_id}", response_model=RecipeBase)
def read_recipe_endpoint(
    *,
    db: Session = Depends(get_db),
    recipe_id: UUID,
):
    db_recipe = recipe_service.get_recipe(db, id=recipe_id)
    if db_recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return db_recipe


@router.get("/", response_model=List[RecipeBase])
def list_recipes_endpoint(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    recipes = recipe_service.get_all_recipes(db, skip=skip, limit=limit)
    return recipes

@router.post("/adapt", response_model=RecipeAdaptationResponse, status_code=status.HTTP_200_OK)
async def adapt_recipe_endpoint(
    request: RecipeAdaptationRequest = Body(...)
):
    try:
        response_from_agent = ai_agents_service.adapt_recipe_interactively(request.model_dump())

        if not isinstance(response_from_agent, dict):
            print(f"Adaptation agent returned an invalid format: {response_from_agent}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI service returned an unexpected response format.")

        if 'error' in response_from_agent:
            print(f"Adaptation agent failed: {response_from_agent.get('details')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"The AI service could not process the adaptation: {response_from_agent.get('details', 'Unknown AI error')}"
            )

        validated_response = RecipeAdaptationResponse(**response_from_agent)

        if validated_response.updated_recipe and validated_response.updated_recipe.ingredients:
            print("Re-calculating nutritional information for adapted recipe...")
            new_nutritional_info = await nutrition_service.nutrition_service.calculate_nutritional_info_for_recipe(
                ingredients=validated_response.updated_recipe.ingredients
            )
            validated_response.updated_recipe.nutrition = new_nutritional_info
            print("Nutritional information for adapted recipe calculated.")

        return validated_response

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected error in /adapt endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing the adaptation request: {str(e)}"
        )
