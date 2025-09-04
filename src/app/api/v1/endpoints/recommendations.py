from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User as UserModel
from app.schemas.recommendation import Recommendation
from app.services.recommendation_service import recommendation_service

router = APIRouter()

@router.get(
    "/",
    response_model=List[Recommendation],
    summary="Get Personalized Recipe Recommendations",
    description="Returns a list of personalized recipes for the currently authenticated user based on their favorites and the behavior of other users."
)
def get_recommendations_endpoint(
    *,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations to return.")
):
    recommendations = recommendation_service.get_recommendations_for_user(
        db=db,
        user_id=current_user.id,
        n_recs=limit
    )
    if not recommendations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not generate recommendations. Add more recipes to your favorites to get started."
        )
    return recommendations