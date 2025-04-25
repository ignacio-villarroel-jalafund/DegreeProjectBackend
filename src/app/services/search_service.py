from duckduckgo_search import DDGS
from typing import List
from app.core.config import settings
from app.schemas.recipe import RecipeSearchResult

SUPPORTED_DOMAINS = [
    "aldi.es/inspirate/recetas", "cookpad.com", "allrecipes.com",
    "bbcgoodfood.com", "foodnetwork.com", "thekitchn.com",
    "tasteofhome.com", "food52.com", "simplyrecipes.com",
    "seriouseats.com", "epicurious.com", "food.com",
    "cocinerosbolivianos.com", "recetascomidas.com", "bonviveur.es",
    "directoalpaladar.com", "recetasgratis.net"
]

SITE_FILTER = " OR ".join(f"site:{d}" for d in SUPPORTED_DOMAINS)

class SearchService:
    def __init__(self, max_results: int = settings.MAX_SEARCH_RESULTS):
        self.max_results = max_results

    def search_recipes(self, query: str) -> List[RecipeSearchResult]:
        query_string = f"{query} ({SITE_FILTER})"
        print(f"\n🔍 Buscando recetas para: '{query}'...")
        results = []
        try:
            with DDGS() as ddgs:
                search_results = ddgs.text(
                    query_string,
                    region='wt-wt',
                    safesearch='off',
                    max_results=self.max_results
                )
                count = 0
                for r in search_results:
                    if r.get("href") and r.get("title") and count < self.max_results:
                        is_supported = any(domain in r["href"] for domain in SUPPORTED_DOMAINS)
                        if is_supported:
                            try:
                                results.append(RecipeSearchResult(title=r["title"], url=r["href"]))
                                count += 1
                            except Exception as pydantic_err:
                                print(f"Resultado de búsqueda inválido: {r['href']} - {pydantic_err}")
                                continue
        except Exception as e:
             print(f"Error durante la búsqueda con DuckDuckGo: {e}")
             return []

        print(f"Encontrados {len(results)} resultados soportados.")
        return results

search_service = SearchService()