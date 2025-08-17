from sqlalchemy import Column, ForeignKey, JSON, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BaseModel

class History(Base, BaseModel):
    __tablename__ = "history"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    recipe_data = Column(JSON, nullable=False)
    source_url = Column(String, index=True, nullable=True)
    is_adapted = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="history_entries")