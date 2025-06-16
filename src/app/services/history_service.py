import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.history import History
from app.repositories.history_repository import history_repository, HistoryRepository
from app.schemas.history import HistoryCreate, HistoryUpdate

class HistoryService:
    def __init__(self, repository: HistoryRepository):
        self.repository = repository

    def add_to_history(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        recipe_data: Dict[str, Any],
        source_url: Optional[str],
        is_adapted: bool
    ) -> History:
        if not source_url:
            history_in_create = HistoryCreate(
                user_id=user_id, recipe_data=recipe_data, source_url=source_url, is_adapted=is_adapted
            )
            return self.repository.create(db=db, obj_in=history_in_create)

        existing_history = self.repository.get_by_user_and_url(db=db, user_id=user_id, url=source_url)

        if existing_history:
            history_in_update = HistoryUpdate(
                recipe_data=recipe_data,
                source_url=source_url,
                is_adapted=is_adapted
            )
            return self.repository.update(db=db, db_obj=existing_history, obj_in=history_in_update)
        else:
            history_in_create = HistoryCreate(
                user_id=user_id, recipe_data=recipe_data, source_url=source_url, is_adapted=is_adapted
            )
            return self.repository.create(db=db, obj_in=history_in_create)

    def get_user_history(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[History]:
        return self.repository.get_by_user(db=db, user_id=user_id, skip=skip, limit=limit)

history_service = HistoryService(history_repository)