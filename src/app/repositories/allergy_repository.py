from app.models.allergy import Allergy
from app.schemas.allergy import AllergyCreate, AllergyUpdate
from app.repositories.base_repository import BaseRepository

class AllergyRepository(BaseRepository[Allergy, AllergyCreate, AllergyUpdate]):
    pass

allergy_repository = AllergyRepository(Allergy)