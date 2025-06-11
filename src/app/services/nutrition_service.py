import httpx
import re
from typing import List, Dict, Optional, Tuple

from app.services.ai_agents_service import ai_agents_service
from app.schemas.recipe import NutritionInfo

class NutritionService:
    def __init__(self):
        self.off_search_url = "https://es.openfoodfacts.org/cgi/search.pl"

    def _parse_ingredient(self, ingredient_str: str) -> Tuple[Optional[float], str]:
        match = re.search(r'(\d[\d\s/.,]*)', ingredient_str)
        quantity = None
        name = ingredient_str.strip()

        if match:
            quantity_str = match.group(1).strip()
            try:
                if '/' in quantity_str:
                    num, den = map(float, quantity_str.split('/'))
                    if den != 0:
                        quantity = num / den
                else:
                    quantity = float(quantity_str.replace(',', '.'))
            except (ValueError, ZeroDivisionError):
                quantity = None
            
            name = ingredient_str.replace(match.group(0), '', 1).strip()
        
        return quantity, name


    async def _get_nutritional_info_from_off(self, ingredient_name: str) -> Optional[Dict]:
        params = {
            "search_terms": ingredient_name,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": 1
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.off_search_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                if data.get('products') and len(data['products']) > 0:
                    product = data['products'][0]
                    return product.get('nutriments')
                return None
            except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
                print(f"Error fetching data from Open Food Facts for '{ingredient_name}': {e}")
                return None

    async def calculate_nutritional_info_for_recipe(self, ingredients: List[str]) -> Optional[NutritionInfo]:
        if not ingredients:
            return None

        ingredient_names_to_search = [self._parse_ingredient(ing)[1] for ing in ingredients]
        enriched_data = ai_agents_service.enrich_ingredients(ingredient_names_to_search)
        
        if 'error' in enriched_data or not enriched_data.get('enriched_ingredients'):
            print("Failed to enrich ingredients. Skipping nutritional calculation.")
            return None

        enriched_ingredients = enriched_data['enriched_ingredients']

        total_nutrition = {
            "calories": 0.0, "protein": 0.0, "carbohydrates": 0.0, "fat": 0.0
        }
        
        for original_ing, enriched_name in zip(ingredients, enriched_ingredients):
            if not enriched_name:
                continue

            nutriments = await self._get_nutritional_info_from_off(enriched_name)
            
            if nutriments:
                total_nutrition["calories"] += nutriments.get('energy-kcal_100g', 0.0)
                total_nutrition["protein"] += nutriments.get('proteins_100g', 0.0)
                total_nutrition["carbohydrates"] += nutriments.get('carbohydrates_100g', 0.0)
                total_nutrition["fat"] += nutriments.get('fat_100g', 0.0)
        
        return NutritionInfo(**total_nutrition)


nutrition_service = NutritionService()