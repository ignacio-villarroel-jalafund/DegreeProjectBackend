from googleapiclient.discovery import build
from typing import List, Dict, Any
from app.core.config import settings
from app.schemas.recipe import RecipeSearchResult
from app.services.ai_agents_service import ai_agents_service
from unidecode import unidecode

class SearchService:
    def __init__(self, max_results: int = settings.MAX_SEARCH_RESULTS):
        self.api_key = settings.GOOGLE_API_KEY
        self.search_engine_id = settings.GOOGLE_SEARCH_ENGINE_ID
        self.max_results = max_results
        self.service = build("customsearch", "v1", developerKey=self.api_key)

    def _build_query_from_analysis(self, analysis: Dict[str, Any]) -> str:
        base_query = analysis.get("base_search", "")
        restrictions = analysis.get("restrictions", [])

        if not base_query:
            return ""

        final_query_parts = [f'"{base_query}"']
        
        for restriction in restrictions:
            term_to_exclude = unidecode(restriction.replace("sin", "").strip().lower())
            
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
            term_to_exclude = unidecode(restriction.replace("sin", "").strip().lower())
            for word in term_to_exclude.split():
                if word:
                    words_to_exclude.add(word)
        
        if not words_to_exclude:
            return items
        
        filtered_items = []
        for item in items:
            text_to_review = f"{item.get('title', '')} {item.get('snippet', '')}".lower()
            text_to_review = unidecode(text_to_review)
            
            if not any(word in text_to_review for word in words_to_exclude):
                filtered_items.append(item)
            else:
                print(f"Descartando resultado: '{item.get('title')}' (Contiene término excluido)")

        return filtered_items

    def search_recipes(self, query: str) -> List[RecipeSearchResult]:        
        analysis_result = ai_agents_service.analyze_search_query(query)
        
        if 'error' in analysis_result:
            print(f"El agente de análisis falló: {analysis_result.get('details', 'Error desconocido')}")
            return []
        
        if not isinstance(analysis_result, dict):
            print(f"Error: La respuesta del agente no es un diccionario válido. Recibido: {analysis_result}")
            return []
        
        analysis_data = analysis_result
        classification = analysis_data.get("clasification", "").upper()

        print(f"Clasificación recibida: '{classification}'")

        if classification == "INVALIDA":
            print("La consulta es inválida según el agente. Búsqueda cancelada.")
            return []
        
        if classification == "CON_RESTRICCION":
            final_query = self._build_query_from_analysis(analysis_data)
            if not final_query:
                print("Error: No se pudo construir una consulta válida desde el análisis.")
                return []
        else:
            final_query = query
                
        results = []
        try:
            num_results_to_fetch = min(self.max_results, 10)
            res = self.service.cse().list(
                q=final_query,
                cx=self.search_engine_id,
                num=num_results_to_fetch,
            ).execute()

            items_to_process = res.get('items', [])
            if classification == "CON_RESTRICCION":
                items_to_process = self._secondary_filter(items_to_process, analysis_data)

            for item in items_to_process:
                image_url = None
                pagemap = item.get('pagemap', {})
                if 'cse_image' in pagemap and pagemap['cse_image']:
                    image_url = pagemap['cse_image'][0].get('src')
                elif 'cse_thumbnail' in pagemap and pagemap['cse_thumbnail']:
                    image_url = pagemap['cse_thumbnail'][0].get('src')

                try:
                    results.append(
                        RecipeSearchResult(
                            title=item['title'],
                            url=item['link'],
                            image_url=image_url
                        )
                    )
                except Exception as pydantic_err:
                    print(f"Resultado de búsqueda inválido: {item.get('link')} - {pydantic_err}")
                    continue

        except Exception as e:
            print(f"Error durante la búsqueda con Google Custom Search API: {e}")
            return []

        print(f"Encontrados {len(results)} resultados finales.")
        return results
    
search_service = SearchService()