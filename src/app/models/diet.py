from sqlalchemy import Column, String
from app.core.database import Base
from app.models.base import BaseModel

class Diet(Base, BaseModel):
    __tablename__ = "diets"

    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)