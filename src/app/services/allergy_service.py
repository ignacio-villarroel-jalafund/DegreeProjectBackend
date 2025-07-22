from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.models.allergy import Allergy
from app.repositories.allergy_repository import allergy_repository, AllergyRepository
from app.schemas.allergy import AllergyCreate, AllergyUpdate

class AllergyService:
    def __init__(self, repository: AllergyRepository):
        self.repository = repository

    def create_allergy(self, db: Session, allergy_in: AllergyCreate) -> Allergy:
        return self.repository.create(db=db, obj_in=allergy_in)

    def get_allergy(self, db: Session, allergy_id: UUID) -> Optional[Allergy]:
        return self.repository.get(db=db, id=allergy_id)

    def get_all_allergies(self, db: Session, skip: int = 0, limit: int = 100) -> List[Allergy]:
        return self.repository.get_multi(db=db, skip=skip, limit=limit)

    def delete_allergy(self, db: Session, allergy_id: UUID) -> Optional[Allergy]:
        return self.repository.remove(db=db, id=allergy_id)

allergy_service = AllergyService(allergy_repository)