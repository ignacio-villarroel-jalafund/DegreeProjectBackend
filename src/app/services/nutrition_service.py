import asyncio
import httpx
import re
from typing import List, Dict, Optional, Tuple

from app.services.ai_agents_service import ai_agents_service
from app.schemas.recipe import NutritionInfo

class NutritionService:
    def __init__(self):
        self.off_search_url = "https://es.openfoodfacts.org/cgi/search.pl"
        self.nutritional_info_cache: Dict[str, Optional[Dict]] = {}
        self.http_client = httpx.AsyncClient(timeout=10)
        self.CONCURRENT_REQUESTS_LIMIT = 2
        self.DELAY_BETWEEN_REQUESTS = 0.5

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
        if ingredient_name in self.nutritional_info_cache:
            print(f"'{ingredient_name}' encontrado en caché.")
            return self.nutritional_info_cache[ingredient_name]

        params = {
            "search_terms": ingredient_name, "search_simple": 1, "action": "process",
            "json": 1, "page_size": 1
        }
        
        try:
            print(f"Buscando en API para: '{ingredient_name}'")
            response = await self.http_client.get(self.off_search_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            nutriments = None
            if data.get('products') and len(data['products']) > 0:
                product = data['products'][0]
                nutriments = product.get('nutriments')

            self.nutritional_info_cache[ingredient_name] = nutriments
            return nutriments

        except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
            print(f"Error fetching data from Open Food Facts for '{ingredient_name}': {e}")
            self.nutritional_info_cache[ingredient_name] = None
            return None

    async def calculate_nutritional_info_for_recipe(self, ingredients: List[str]) -> Optional[NutritionInfo]:
        if not ingredients:
            return None

        ingredient_names_to_search = [self._parse_ingredient(ing)[1] for ing in ingredients]
        enriched_data = ai_agents_service.enrich_ingredients(ingredient_names_to_search)
        
        if 'error' in enriched_data or 'ingredients' not in enriched_data:
            print("Error en la respuesta de n8n o la clave 'ingredients' no se encontró.")
            return None

        enriched_ingredients_list = enriched_data.get('ingredients', [])
        if not enriched_ingredients_list or not isinstance(enriched_ingredients_list, list):
            print("La lista 'ingredients' de n8n está vacía o no es una lista válida.")
            return None

        semaphore = asyncio.Semaphore(self.CONCURRENT_REQUESTS_LIMIT)
        tasks = []

        async def fetch_with_semaphore(ingredient_name: str) -> Optional[Dict]:
            async with semaphore:
                await asyncio.sleep(self.DELAY_BETWEEN_REQUESTS)
                return await self._get_nutritional_info_from_off(ingredient_name)

        unique_ingredient_names = {
            item['name'] for item in enriched_ingredients_list if isinstance(item, dict) and item.get('name')
        }
        
        for name in unique_ingredient_names:
            tasks.append(fetch_with_semaphore(name))
        
        results = await asyncio.gather(*tasks)

        total_nutrition = {"calories": 0.0, "protein": 0.0, "carbohydrates": 0.0, "fat": 0.0}
        
        for nutriments in results:
            if nutriments:
                total_nutrition["calories"] += float(nutriments.get('energy-kcal_100g', 0.0) or 0.0)
                total_nutrition["protein"] += float(nutriments.get('proteins_100g', 0.0) or 0.0)
                total_nutrition["carbohydrates"] += float(nutriments.get('carbohydrates_100g', 0.0) or 0.0)
                total_nutrition["fat"] += float(nutriments.get('fat_100g', 0.0) or 0.0)
        
        return NutritionInfo(**total_nutrition)

nutrition_service = NutritionService()