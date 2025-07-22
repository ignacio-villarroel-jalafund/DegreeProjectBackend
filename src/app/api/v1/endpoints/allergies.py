from typing import List
from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.schemas.allergy import AllergyRead, AllergyCreate
from app.services.allergy_service import allergy_service

router = APIRouter()

@router.post("/", response_model=AllergyRead, status_code=status.HTTP_201_CREATED)
def create_allergy_endpoint(*, db: Session = Depends(get_db), allergy_in: AllergyCreate):
    return allergy_service.create_allergy(db=db, allergy_in=allergy_in)

@router.get("/", response_model=List[AllergyRead])
def list_allergies_endpoint(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return allergy_service.get_all_allergies(db, skip=skip, limit=limit)

@router.delete("/{allergy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_allergy_endpoint(*, db: Session = Depends(get_db), allergy_id: UUID):
    allergy = allergy_service.get_allergy(db, allergy_id)
    if not allergy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allergy not found")
    allergy_service.delete_allergy(db, allergy_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)