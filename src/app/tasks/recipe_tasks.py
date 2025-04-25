from typing import Dict, Any

import httpx
from recipe_scrapers import scrape_me, _exceptions as ScraperExceptions
from app.celery.celery_app import celery_app
from app.services.analysis_service import analysis_service
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def analyze_and_return(self, scraped_data_dict: Dict[str, Any]) -> Dict[str, Any]:
    task_id = self.request.id
    recipe_name = scraped_data_dict.get("recipe_name", "Nombre Desconocido")
    print(f"[{task_id}] Iniciando ANÁLISIS para receta: {recipe_name}")

    if  not recipe_name:
        message = "Datos scrapeados incompletos (recipe_name)."
        print(f"[{task_id}] {message}")
        self.update_state(state='FAILURE', meta={'exc_type': 'ValueError', 'exc_message': message})
        return {"status": "FAILURE", "message": message}

    try:
        print(f"[{task_id}] Analizando receta...")
        analysis_text = analysis_service.analyze_recipe(scraped_data_dict)
        status = "SUCCESS"
        message = f"Análisis completado para {recipe_name}."
        print(f"[{task_id}] Análisis finalizado.")
    except Exception as exc:
        status = "FAILURE"
        analysis_text = None
        message = f"Error durante el análisis: {exc}"
        print(f"[{task_id}] {message}")
        self.update_state(state='FAILURE', meta={'exc_type': type(exc).__name__, 'exc_message': str(exc)})

    return {
        "status": status,
        "analysis": analysis_text,
        "message": message
    }

async def scrape_url_data(url: str) -> Dict[str, Any]:
    print(f"Iniciando scraping para URL: {url}")

    if not is_valid_url(url):
         print(f"URL inválida: {url}")
         raise ValueError("URL inválida")

    try:
        async with httpx.AsyncClient() as client:
             response = await client.head(url, follow_redirects=True, timeout=15.0)
             response.raise_for_status()

        print(f"Extrayendo datos estructurados de: {url}")
        scraper = scrape_me(url)

        title = scraper.title()
        ingredients = scraper.ingredients()
        instructions = scraper.instructions_list()

        if not title or (not ingredients and not instructions):
             raise ValueError("Datos scrapeados insuficientes (falta título o ingredientes/instrucciones)")

        scraped_data = {
            "recipe_name": title,
            "ingredients": ingredients,
            "directions": instructions,
            "url": url,
            "img_src": scraper.image(),
        }

        print(f"Scraping exitoso para: {scraped_data.get('recipe_name')}")
        return scraped_data

    except httpx.RequestError as http_err:
        print(f"Error de red al acceder a la URL {url}: {http_err}")
        raise ConnectionError(f"No se pudo acceder a la URL: {http_err}") from http_err
    except (ScraperExceptions.WebsiteNotImplementedError, ScraperExceptions.NoSchemaFoundInWildMode) as scrape_err:
        error_type = type(scrape_err).__name__
        print(f"Error de scraping (tipo específico) en {url}: ({error_type}) {scrape_err}")
        raise ValueError(f"Error de scraping ({error_type}): {scrape_err}") from scrape_err
    except ValueError as val_err:
         print(f"Error de validación de datos scrapeados en {url}: {val_err}")
         raise
    except Exception as e:
        error_type = type(e).__name__
        print(f"Error inesperado durante el scraping de {url}: ({error_type}) {e}")
        raise RuntimeError(f"Error inesperado de scraping: {e}") from e

