from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.location_service import location_service
from app.schemas.location import SubdivisionResponse

router = APIRouter()

@router.get(
    "/subdivisions",
    response_model=SubdivisionResponse,
    summary="Get administrative subdivisions for a country",
    description="Retrieves a list of first-level administrative subdivisions (like states or departments) for a given country name or ISO code."
)
def get_country_subdivisions(
    country: str = Query(..., description="Country name (e.g., 'Bolivia') or ISO 3166-1 alpha-2 code (e.g., 'BO')."),
    lang: Optional[str] = Query('es', description="Language code for subdivision names (e.g., 'es', 'en'). Defaults to 'es'.")
):
    if not location_service.geonames_user:
        raise HTTPException(
            status_code=503,
            detail="Location service is not configured (GeoNames username missing)."
        )

    subdivision_names = location_service.get_subdivision_names_country(country_name_or_code=country, lang=lang)

    if subdivision_names is None:
        raise HTTPException(
            status_code=404,
            detail=f"Could not retrieve subdivisions for country '{country}'. The country might not be found or there was an issue with the external service."
        )
    
    if not subdivision_names:
        return SubdivisionResponse(
            country_queried=country,
            subdivisions=[],
            message=f"No first-level administrative subdivisions found for '{country}' with language '{lang}', or the country does not have them."
        )

    return SubdivisionResponse(
        country_queried=country,
        subdivisions=subdivision_names
    )
