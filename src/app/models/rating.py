from sqlalchemy import Column, Float, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BaseModel

class Rating(Base, BaseModel):
    __tablename__ = "ratings"

    score = Column(Float, nullable=False) 
    comment = Column(Text, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=False)

    user = relationship("User", back_populates="ratings")
    recipe = relationship("Recipe", back_populates="ratings")

    __table_args__ = (UniqueConstraint('user_id', 'recipe_id', name='uq_user_recipe_rating'),)
