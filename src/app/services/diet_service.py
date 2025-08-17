from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.models.diet import Diet
from app.repositories.diet_repository import diet_repository, DietRepository
from app.schemas.diet import DietCreate, DietUpdate

class DietService:
    def __init__(self, repository: DietRepository):
        self.repository = repository

    def create_diet(self, db: Session, diet_in: DietCreate) -> Diet:
        return self.repository.create(db=db, obj_in=diet_in)

    def get_diet(self, db: Session, diet_id: UUID) -> Optional[Diet]:
        return self.repository.get(db=db, id=diet_id)

    def get_all_diets(self, db: Session, skip: int = 0, limit: int = 100) -> List[Diet]:
        return self.repository.get_multi(db=db, skip=skip, limit=limit)

    def delete_diet(self, db: Session, diet_id: UUID) -> Optional[Diet]:
        return self.repository.remove(db=db, id=diet_id)

diet_service = DietService(diet_repository)