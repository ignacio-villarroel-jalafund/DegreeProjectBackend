import httpx
from typing import List, Optional
from app.core.config import settings
from app.schemas.recipe import NutritionInfo
from app.services.ai_agents_service import ai_agents_service

class NutritionService:
    def __init__(self):
        self.api_url = "https://api.api-ninjas.com/v1/nutrition"
        self.api_key = settings.API_NINJAS_KEY
        self.http_client = httpx.AsyncClient(timeout=20)

    async def calculate_nutritional_info_for_recipe(self, ingredients: List[str]) -> Optional[NutritionInfo]:
        if not ingredients:
            print("No ingredients provided to calculate nutritional info.")
            return None

        enriched = ai_agents_service.enrich_ingredients(ingredients=ingredients)
        items = enriched.get("ingr", [])
        if not items:
            print("Ingredient parsing returned vacío.")
            return None

        query = " and ".join(items)
        headers = {"X-Api-Key": self.api_key}

        try:
            print("Ingredientes antes de información nutricional", query)
            resp = await self.http_client.get(self.api_url, params={"query": query}, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            if not isinstance(data, list) or not data:
                print("Respuesta inesperada o vacía de API Ninjas:", data)
                return None

            total = NutritionInfo()
            for item in data:
                total.fat_total_g += float(item.get("fat_total_g", 0) or 0)
                total.fat_saturated_g += float(item.get("fat_saturated_g", 0) or 0)
                total.carbohydrates_total_g += float(item.get("carbohydrates_total_g", 0) or 0)
                total.fiber_g += float(item.get("fiber_g", 0) or 0)
                total.sugar_g += float(item.get("sugar_g", 0) or 0)
                total.sodium_mg += float(item.get("sodium_mg", 0) or 0)
                total.potassium_mg += float(item.get("potassium_mg", 0) or 0)
                total.cholesterol_mg += float(item.get("cholesterol_mg", 0) or 0)

            print("Nutritional info computed successfully via API Ninjas.")
            print("Información nutricional", total)
            return total

        except httpx.HTTPStatusError as e:
            print(f"HTTP error from API Ninjas ({e.response.status_code}):", e.response.text)
            return None
        except Exception as e:
            print("Error calling API Ninjas Nutrition API:", e)
            return None

nutrition_service = NutritionService()
