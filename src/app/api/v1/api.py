from fastapi import APIRouter
from app.api.v1.endpoints import tasks, users, recipes

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(recipes.router, prefix="/recipes", tags=["recipes"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks Status"])