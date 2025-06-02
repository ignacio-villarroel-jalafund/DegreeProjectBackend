from pydantic import BaseModel
from typing import List, Optional

class SubdivisionResponse(BaseModel):
    country_queried: str
    subdivisions: List[str]
    message: Optional[str] = None

    class Config:
        from_attributes = True
