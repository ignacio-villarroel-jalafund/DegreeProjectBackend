from fastapi import APIRouter
from app.api.v1.endpoints import locations, supermarkets, tasks, users, recipes

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(recipes.router, prefix="/recipes", tags=["recipes"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks status"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(supermarkets.router, prefix="/supermarkets", tags=["supermarkets"])
