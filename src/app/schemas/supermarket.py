from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Union

class SupermarketInfo(BaseModel):
    place_id: str
    name: str
    address: str
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    website: Optional[HttpUrl] = None
    phone_number: Optional[str] = None
    opening_hours_periods: Optional[List[str]] = None
    icon_url: Optional[HttpUrl] = None
    Maps_url: Optional[HttpUrl] = None
    photo_url: Optional[HttpUrl] = None

    class Config:
        from_attributes = True

class SupermarketSearchResponse(BaseModel):
    query_location: str
    supermarkets: List[SupermarketInfo]
    message: Optional[str] = None
    next_page_token: Optional[str] = None

    class Config:
        from_attributes = True
