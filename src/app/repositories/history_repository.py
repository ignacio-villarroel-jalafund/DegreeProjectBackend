from typing import List, Optional
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.models.history import History
from app.schemas.history import HistoryCreate, HistoryUpdate
from app.repositories.base_repository import BaseRepository

class HistoryRepository(BaseRepository[History, HistoryCreate, HistoryUpdate]):

    def get_by_user_and_url(self, db: Session, *, user_id: uuid.UUID, url: str) -> Optional[History]:
        return db.query(self.model).filter(
            self.model.user_id == user_id, 
            self.model.source_url == url
        ).first()

    def get_by_user(self, db: Session, *, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[History]:
        return db.query(self.model).filter(self.model.user_id == user_id).order_by(
            desc(func.coalesce(self.model.updated_at, self.model.created_at))
        ).offset(skip).limit(limit).all()

history_repository = HistoryRepository(History)
