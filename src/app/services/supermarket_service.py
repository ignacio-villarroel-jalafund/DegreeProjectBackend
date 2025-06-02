import requests
from typing import List, Optional, Dict, Any, Tuple
from app.core.config import settings
from app.schemas.supermarket import SupermarketInfo

class SupermarketService:
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.base_url = settings.GOOGLE_MAPS_API_BASE_URL

        if not self.api_key:
            print("CRITICAL ERROR: Maps_API_KEY is not set in settings.")
        if not self.base_url:
            print("CRITICAL ERROR: Maps_API_BASE_URL is not set in settings.")

    def _check_config(self) -> bool:
        if not self.api_key or not self.base_url:
            print("Error: SupermarketService is not properly configured (API key or base URL missing).")
            return False
        return True

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self._check_config():
            return None
        try:
            log_param = params.get('place_id') or params.get('query') or params.get('pagetoken', 'N/A')
            print(f"Making request to: {self.base_url}/{endpoint} with main param: {log_param}")
            response = requests.get(f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("status") not in ["OK", "ZERO_RESULTS", "INVALID_REQUEST"]:
                print(f"Google Maps API Error ({data.get('status')}): {data.get('error_message', 'No error message')}")
                if data.get("status") == "REQUEST_DENIED" and "You must enable Billing" in data.get('error_message', ''):
                    print("CRITICAL: Billing is not enabled for the Google Cloud project or API key is restricted.")
                return None
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error during request to Google Maps API ({endpoint}): {e}")
            return None
        except ValueError:
            print(f"Error decoding JSON response from Google Maps API ({endpoint}). Response: {response.text if 'response' in locals() else 'No response'}")
            return None

    def find_supermarkets(
        self,
        city: Optional[str] = None,
        country: Optional[str] = None,
        lang: str = 'es',
        limit_details_per_page: int = 5,
        page_token: Optional[str] = None
    ) -> Tuple[List[SupermarketInfo], Optional[str]]:
        if not self._check_config():
            return [], None

        text_search_endpoint = "place/textsearch/json"
        search_data: Optional[Dict[str, Any]]

        if page_token:
            print(f"SupermarketService: Performing Text Search using page_token: '{page_token}'")
            text_search_params = {
                "pagetoken": page_token,
                "key": self.api_key
            }
        elif city and country:
            query = f"supermercados en {city}, {country}"
            print(f"SupermarketService: Performing Text Search for query: '{query}' with lang '{lang}'")
            text_search_params = {
                "query": query,
                "key": self.api_key,
                "language": lang,
                "type": "supermarket"
            }
        else:
            print("SupermarketService: Error - City and Country must be provided for an initial search if no page_token is given.")
            return [], None

        search_data = self._make_request(text_search_endpoint, text_search_params)

        if not search_data:
            print(f"SupermarketService: Text Search request failed completely.")
            return [], None

        if search_data.get("status") == "INVALID_REQUEST" and page_token:
            print(f"SupermarketService: Text Search with page_token '{page_token}' resulted in INVALID_REQUEST. Token might be expired or invalid.")
            return [], None

        if search_data.get("status") == "ZERO_RESULTS":
            print(f"SupermarketService: No results from Text Search for the given query/page_token. Status: ZERO_RESULTS")
            return [], search_data.get("next_page_token")

        if not search_data.get("results"):
            print(f"SupermarketService: No 'results' array in Text Search response despite OK status. Status: {search_data.get('status')}")
            return [], search_data.get("next_page_token")

        next_page_token_from_api = search_data.get("next_page_token")
        place_ids = [place.get("place_id") for place in search_data["results"] if place.get("place_id")]

        if not place_ids:
            print(f"SupermarketService: No place_ids found in Text Search results for this page.")
            return [], next_page_token_from_api

        place_ids_to_detail = place_ids[:limit_details_per_page]
        print(f"SupermarketService: Text Search returned {len(place_ids)} place IDs, fetching details for {len(place_ids_to_detail)}.")

        supermarkets_info: List[SupermarketInfo] = []
        details_endpoint = "place/details/json"
        fields_to_request = "place_id,name,formatted_address,website,international_phone_number,opening_hours,rating,user_ratings_total,icon,url,photos"

        for place_id in place_ids_to_detail:
            details_params = {
                "place_id": place_id,
                "key": self.api_key,
                "language": lang,
                "fields": fields_to_request
            }

            print(f"SupermarketService: Fetching details for place_id: {place_id}")
            details_data = self._make_request(details_endpoint, details_params)

            if details_data and details_data.get("result"):
                result = details_data["result"]

                opening_hours_periods = None
                if result.get("opening_hours") and result["opening_hours"].get("weekday_text"):
                    opening_hours_periods = result["opening_hours"]["weekday_text"]

                Maps_url_val = result.get("url")
                if not Maps_url_val:
                    Maps_url_val = f"https://www.google.com/maps/search/?api=1&query=Google&query_place_id={result.get('place_id')}"

                photo_url_val = None
                if result.get("photos") and isinstance(result["photos"], list) and len(result["photos"]) > 0:
                    photo_reference = result["photos"][0].get("photo_reference")
                    max_width = 400
                    if photo_reference:
                        photo_url_val = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={max_width}&photoreference={photo_reference}&key={self.api_key}"

                supermarket = SupermarketInfo(
                    place_id=result.get("place_id"),
                    name=result.get("name"),
                    address=result.get("formatted_address"),
                    rating=result.get("rating"),
                    user_ratings_total=result.get("user_ratings_total"),
                    website=result.get("website"),
                    phone_number=result.get("international_phone_number"),
                    opening_hours_periods=opening_hours_periods,
                    icon_url=result.get("icon"),
                    Maps_url=Maps_url_val,
                    photo_url=photo_url_val
                )
                supermarkets_info.append(supermarket)
            else:
                print(f"SupermarketService: Could not fetch details for place_id {place_id}. Status: {details_data.get('status') if details_data else 'N/A'}")

        print(f"SupermarketService: Successfully fetched details for {len(supermarkets_info)} supermarkets for this page.")
        return supermarkets_info, next_page_token_from_api

supermarket_service = SupermarketService()
