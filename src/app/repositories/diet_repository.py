from app.models.diet import Diet
from app.schemas.diet import DietCreate, DietUpdate
from app.repositories.base_repository import BaseRepository

class DietRepository(BaseRepository[Diet, DietCreate, DietUpdate]):
    pass

diet_repository = DietRepository(Diet)