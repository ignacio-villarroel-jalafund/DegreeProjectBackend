from sqlalchemy import Column, String, Text, Float, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BaseModel


class Recipe(Base, BaseModel):
    __tablename__ = "recipes"

    recipe_name = Column(String, index=True, nullable=False)
    servings = Column(Integer, nullable=True)
    ingredients = Column(Text, nullable=False)
    directions = Column(Text, nullable=False)
    url = Column(String, nullable=True)
    cuisine_path = Column(String, nullable=True)
    nutrition = Column(Text, nullable=True)
    timing = Column(Text, nullable=True)
    img_src = Column(String, nullable=True)

    favorited_by = relationship("Favorite", back_populates="recipe", cascade="all, delete-orphan")
