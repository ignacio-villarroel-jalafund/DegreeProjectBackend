from typing import List
import uuid
from sqlalchemy.orm import Session
from app.models.history import History
from app.schemas.history import HistoryCreate
from app.repositories.base_repository import BaseRepository

class HistoryRepository(BaseRepository[History, HistoryCreate, None]):
    def get_by_user(self, db: Session, *, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[History]:
        return db.query(self.model).filter(self.model.user_id == user_id).order_by(self.model.created_at.desc()).offset(skip).limit(limit).all()

history_repository = HistoryRepository(History)