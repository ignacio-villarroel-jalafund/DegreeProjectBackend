from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.supermarket_service import supermarket_service
from app.schemas.supermarket import SupermarketSearchResponse

router = APIRouter()

@router.get(
    "/supermarkets",
    response_model=SupermarketSearchResponse,
    summary="Search for supermarkets by location or page token",
    description="Retrieves a list of supermarkets. Provide 'ciudad' and 'pais' for an initial search, or a 'page_token' from a previous search to get the next set of results. Includes photo URLs if available."
)
def search_supermarkets_endpoint(
    ciudad: Optional[str] = Query(None, description="City name (e.g., 'Cochabamba'). Required for initial search if 'page_token' is not provided."),
    pais: Optional[str] = Query(None, description="Country name (e.g., 'Bolivia'). Required for initial search if 'page_token' is not provided."),
    lang: Optional[str] = Query('es', description="Language code for results (e.g., 'es', 'en'). Defaults to 'es'."),
    page_token: Optional[str] = Query(None, description="Token from a previous search to fetch the next page of results."),
    limit_details: Optional[int] = Query(5, ge=1, le=20, description="Number of detailed results to fetch per API call.")
):
    if not supermarket_service.api_key or not supermarket_service.base_url:
        raise HTTPException(
            status_code=503,
            detail="Supermarket service is not configured (Google Maps API key or base URL missing)."
        )

    if not page_token and (not ciudad or not pais):
        raise HTTPException(
            status_code=400,
            detail="For an initial search, 'ciudad' and 'pais' query parameters are required. Alternatively, provide a 'page_token' for subsequent results."
        )
    
    found_supermarkets, next_page_token_from_service = supermarket_service.find_supermarkets(
        city=ciudad, country=pais, lang=lang, page_token=page_token, limit_details_per_page=limit_details
    )
    
    query_location_display: str
    if page_token:
        query_location_display = f"Paginated results for previous search"
        if ciudad and pais:
             query_location_display = f"{ciudad}, {pais} (Page via token)"
    elif ciudad and pais:
        query_location_display = f"{ciudad}, {pais}"
    else:
        query_location_display = "Supermarket search"

    response_message: Optional[str] = None
    if not found_supermarkets:
        if page_token:
            response_message = f"No more supermarkets found for the ongoing search query. Language: '{lang}'."
        else:
            response_message = f"No supermarkets found for '{query_location_display}' with language '{lang}', or there was an issue with the external service."
    
    return SupermarketSearchResponse(
        query_location=query_location_display,
        supermarkets=found_supermarkets,
        next_page_token=next_page_token_from_service,
        message=response_message
    )
