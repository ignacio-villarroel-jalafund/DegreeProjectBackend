from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    OLLAMA_HOST: str
    OLLAMA_MODEL: str

    MAX_SEARCH_RESULTS: int
    RECIPE_DOMAINS: Optional[str] = None

    REDIS_HOST: str
    REDIS_PORT: int

    GOOGLE_API_KEY: str
    GOOGLE_SEARCH_RECIPE_ENGINE_ID: str
    GOOGLE_SEARCH_INGREDIENT_ENGINE_ID: str

    GEONAMES_USERNAME: str
    GEONAMES_API_BASE_URL: str

    GOOGLE_MAPS_API_KEY: str
    GOOGLE_MAPS_API_BASE_URL: str

    N8N_BASE_URL: str

    EDAMAM_APP_ID: str
    EDAMAM_APP_KEY: str
    EDAMAM_NUTRITION_API_URL: str

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'ignore'


settings = Settings()
