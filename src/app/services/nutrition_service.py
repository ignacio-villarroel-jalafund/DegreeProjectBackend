import httpx
from typing import List, Optional

from app.core.config import settings
from app.schemas.recipe import NutritionInfo
from app.services.ai_agents_service import ai_agents_service

class NutritionService:
    def __init__(self):
        self.api_url = settings.EDAMAM_NUTRITION_API_URL
        self.app_id = settings.EDAMAM_APP_ID
        self.app_key = settings.EDAMAM_APP_KEY
        self.http_client = httpx.AsyncClient(timeout=20)

    async def calculate_nutritional_info_for_recipe(self, ingredients: List[str]) -> Optional[NutritionInfo]:
        if not ingredients:
            print("No ingredients provided to calculate nutritional info.")
            return None
        
        clean_ingredients_response = ai_agents_service.enrich_ingredients(ingredients=ingredients)

        clean_ingredients_list = clean_ingredients_response.get('ingr', [])

        if not clean_ingredients_list:
            print("Cleaned ingredient list is empty after processing.")
            return None
        
        payload = {"ingr": clean_ingredients_list}
        params = {"app_id": self.app_id, "app_key": self.app_key}
        try:
            response = await self.http_client.post(self.api_url, json=payload, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if "ingredients" not in data or not data["ingredients"]:
                print("Edamam response does not contain parsed ingredients data.")
                print(f"Full Edamam response data: {data}")
                return None

            total_nutrition = {
                "calories": 0.0,
                "protein": 0.0,
                "carbohydrates": 0.0,
                "fat": 0.0
            }

            for ingredient_data in data["ingredients"]:
                if ingredient_data.get("parsed"):
                    parsed_info = ingredient_data["parsed"][0]
                    nutrients = parsed_info.get("nutrients", {})
                    
                    total_nutrition["calories"] += nutrients.get("ENERC_KCAL", {}).get("quantity", 0.0)
                    total_nutrition["protein"] += nutrients.get("PROCNT", {}).get("quantity", 0.0)
                    total_nutrition["carbohydrates"] += nutrients.get("CHOCDF", {}).get("quantity", 0.0)
                    total_nutrition["fat"] += nutrients.get("FAT", {}).get("quantity", 0.0)
            
            print("Nutritional information successfully calculated by summing individual ingredients.")
            return NutritionInfo(**total_nutrition)

        except httpx.HTTPStatusError as e:
            response_text = e.response.text
            print(f"Error from Edamam API ({e.response.status_code}): {response_text}")
            if e.response.status_code == 422:
                 print("Edamam Error Detail: Could not parse one or more ingredients.")
            elif e.response.status_code == 401:
                 print("Edamam Error Detail: Invalid credentials (app_id or app_key).")
            return None
        except (httpx.RequestError, ValueError) as e:
            print(f"Error calling Edamam Nutrition API: {e}")
            return None

nutrition_service = NutritionService()
