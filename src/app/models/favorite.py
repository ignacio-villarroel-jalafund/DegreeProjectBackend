from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BaseModel

class Favorite(Base, BaseModel):
    __tablename__ = "favorites"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=False)

    user = relationship("User", back_populates="favorites")
    recipe = relationship("Recipe", back_populates="favorited_by")

    __table_args__ = (UniqueConstraint('user_id', 'recipe_id', name='uq_user_recipe_favorite'),)