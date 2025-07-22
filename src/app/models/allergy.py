from sqlalchemy import Column, String
from app.core.database import Base
from app.models.base import BaseModel

class Allergy(Base, BaseModel):
    __tablename__ = "allergies"

    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)