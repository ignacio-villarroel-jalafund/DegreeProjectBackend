from googleapiclient.discovery import build
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.services.ai_agents_service import ai_agents_service
from unidecode import unidecode


class SearchService:
    def __init__(self, max_results: int = settings.MAX_SEARCH_RESULTS):
        self.api_key = settings.GOOGLE_API_KEY
        self.search_recipe_engine_id = settings.GOOGLE_SEARCH_RECIPE_ENGINE_ID
        self.search_ingredient_engine_id = settings.GOOGLE_SEARCH_INGREDIENT_ENGINE_ID
        self.max_results = max_results
        self.service = build("customsearch", "v1", developerKey=self.api_key)

    def _build_query_from_analysis(self, analysis: Dict[str, Any]) -> str:
        base_query = analysis.get("base_search", "")
        restrictions = analysis.get("restrictions", [])

        if not base_query:
            return ""

        final_query_parts = [f'"{base_query}"']

        for restriction in restrictions:
            term_to_exclude = unidecode(
                restriction.replace("sin", "").strip().lower())

            for word in term_to_exclude.split():
                if word:
                    final_query_parts.append(f'-{word}')

        final_query = " ".join(final_query_parts)
        return final_query

    def _secondary_filter(self, items: List[Dict[str, Any]], analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        restrictions = analysis.get("restrictions", [])
        if not restrictions:
            return items

        words_to_exclude = set()
        for restriction in restrictions:
            term_to_exclude = unidecode(
                restriction.replace("sin", "").strip().lower())
            for word in term_to_exclude.split():
                if word:
                    words_to_exclude.add(word)

        if not words_to_exclude:
            return items

        filtered_items = []
        for item in items:
            text_to_review = f"{item.get('title', '')} {item.get('snippet', '')}".lower(
            )
            text_to_review = unidecode(text_to_review)

            if not any(word in text_to_review for word in words_to_exclude):
                filtered_items.append(item)
            else:
                print(
                    f"Discarding result: '{item.get('title')}' (Contains excluded term)")

        return filtered_items

    def search_recipes(self, query: str, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        analysis_result = ai_agents_service.analyze_search_query(query)

        if isinstance(analysis_result, dict) and 'error' in analysis_result:
            print(
                f"Analysis agent failed: {analysis_result.get('details', 'Unknown error')}")
            return []

        if not isinstance(analysis_result, dict):
            print(
                f"Error: Agent response is not a valid dictionary. Received: {analysis_result}")
            return []

        analysis_data = analysis_result
        classification = analysis_data.get("clasification", "").upper()

        print(f"Classification received: '{classification}'")

        if classification == "INVALIDA":
            print("Query is invalid according to the agent. Search cancelled.")
            return []

        if classification == "CON_RESTRICCION":
            final_query = self._build_query_from_analysis(analysis_data)
            if not final_query:
                print("Error: Could not build a valid query from the analysis.")
                return []
        else:
            final_query = query

        results = []
        try:
            num_results_to_fetch = min(limit, 10)
            start_index = skip + 1

            print(f"Searching for recipes with query: '{final_query}' using engine ID: {self.search_recipe_engine_id}")
            res = self.service.cse().list(
                q=final_query,
                cx=self.search_recipe_engine_id,
                num=num_results_to_fetch,
                start=start_index,
            ).execute()

            items_to_process = res.get('items', [])
            if classification == "CON_RESTRICCION":
                items_to_process = self._secondary_filter(
                    items_to_process, analysis_data)

            for item in items_to_process:
                image_url = None
                pagemap = item.get('pagemap', {})
                if pagemap:
                    if 'cse_image' in pagemap and pagemap['cse_image']:
                        image_url = pagemap['cse_image'][0].get('src')
                    elif 'cse_thumbnail' in pagemap and pagemap['cse_thumbnail']:
                        image_url = pagemap['cse_thumbnail'][0].get('src')

                results.append({
                    "title": item.get('title'),
                    "url": item.get('link'),
                    "image_url": image_url
                })


        except Exception as e:
            print(f"Error during Google Custom Search API call for recipes: {e}")
            return []

        print(f"Found {len(results)} recipe results.")
        return results

    def get_ingredient(self, text_query: str) -> Optional[Dict[str, Any]]:
        print(f"Attempting to extract ingredient from query: '{text_query}'")
        ingredient_name: Optional[str] = None
        try:
            extraction_result = ai_agents_service.extract_ingredient(text_query)
        except Exception as e:
            print(f"Error calling ingredient extraction agent service: {e}")
            return None

        if not isinstance(extraction_result, dict):
            print(f"Error: Ingredient extraction agent response is not a valid dictionary. Received: {extraction_result}")
            return None

        if 'error' in extraction_result:
            print(f"Ingredient extraction agent failed: {extraction_result.get('details', 'Unknown error')}")
            return None

        if "ingredient" not in extraction_result:
            print(f"Error: 'ingredient' key missing in agent response. Received: {extraction_result}")
            return None

        ingredient_name = extraction_result.get("ingredient")

        print("Nombre ingrediente:", ingredient_name)

        if not isinstance(ingredient_name, str) or not ingredient_name.strip():
            print(f"Ingredient extraction agent returned an invalid or empty ingredient: '{ingredient_name}'")
            return None

        print(f"Successfully extracted ingredient by AI: '{ingredient_name}'")
        print(f"Now searching Google for ingredient: '{ingredient_name}' using engine ID: {self.search_ingredient_engine_id}")

        search_query = f"{ingredient_name} ingrediente -receta -preparación -cocina -shampoo -cosmético -belleza"

        try:
            res = self.service.cse().list(
                q=search_query,
                cx=self.search_ingredient_engine_id,
                num=1,
                searchType="image",
                imgType="photo",
                lr="lang_es",
                hl="es",
                safe="active"
            ).execute()

            items = res.get('items', [])
            if items:
                first_item = items[0]
                image_url = first_item.get('link')
                page_url = first_item.get('image', {}).get('contextLink')

                print(f"Found image for '{ingredient_name}': {image_url} from page: {page_url}")
                return {
                    "name": ingredient_name,
                    "image_url": image_url,
                    "search_url": page_url
                }
            else:
                print(f"No image results found on Google for ingredient: '{ingredient_name}'")
                return {
                    "name": ingredient_name,
                    "image_url": None,
                    "search_url": None
                }

        except Exception as e:
            print(f"Error during Google Custom Search API call for ingredient image: {e}")
            return {
                "name": ingredient_name,
                "image_url": None,
                "search_url": None
            }


search_service = SearchService()
