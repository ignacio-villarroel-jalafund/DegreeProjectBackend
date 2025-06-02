from typing import Optional
from pydantic import BaseModel, HttpUrl

class IngredientInfoResponse(BaseModel):
    name: Optional[str] = None
    image_url: Optional[HttpUrl] = None
    search_url: Optional[HttpUrl] = None
    