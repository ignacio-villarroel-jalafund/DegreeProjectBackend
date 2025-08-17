from typing import List
from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.schemas.diet import DietRead, DietCreate
from app.services.diet_service import diet_service

router = APIRouter()

@router.post("/", response_model=DietRead, status_code=status.HTTP_201_CREATED)
def create_diet_endpoint(*, db: Session = Depends(get_db), diet_in: DietCreate):
    return diet_service.create_diet(db=db, diet_in=diet_in)

@router.get("/", response_model=List[DietRead])
def list_diets_endpoint(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return diet_service.get_all_diets(db, skip=skip, limit=limit)

@router.delete("/{diet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_diet_endpoint(*, db: Session = Depends(get_db), diet_id: UUID):
    diet = diet_service.get_diet(db, diet_id)
    if not diet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diet not found")
    diet_service.delete_diet(db, diet_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)