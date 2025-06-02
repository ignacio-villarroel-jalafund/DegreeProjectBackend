from typing import Dict, Any
from urllib.parse import urlparse

import httpx
from recipe_scrapers import scrape_me, _exceptions as ScraperExceptions

class ScrapingService:
    """
    Un servicio dedicado a realizar el scraping de recetas desde URLs.
    Encapsula la lógica de validación, petición de red y extracción de datos de forma robusta.
    """

    def _is_valid_url(self, url: str) -> bool:
        """Verifica si una URL tiene el formato correcto."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except (ValueError, AttributeError):
            return False

    async def scrape_recipe_from_url(self, url: str) -> Dict[str, Any]:
        """
        Realiza el scraping de una URL. No falla si faltan campos opcionales, pero
        lanza un ValueError si faltan campos obligatorios (título, imagen, ingredientes, pasos).

        Args:
            url: La URL de la receta a scrapear.

        Returns:
            Un diccionario con los datos de la receta.
        """
        print(f"Servicio de Scraping: Iniciando para URL: {url}")

        if not self._is_valid_url(url):
            raise ValueError("La URL proporcionada no es válida.")

        try:
            scraper = scrape_me(url=url)
            # --- 1. FASE DE EXTRACCIÓN (Tolerante a errores) ---
            
            # Campos obligatorios
            title = scraper.title()
            image_url = scraper.image()
            ingredients = scraper.ingredients()
            directions = scraper.instructions_list()

            # Campos opcionales (tiempos) - los envolvemos en try/except
            # para capturar errores como SchemaOrgException sin detener el proceso.
            try:
                cook_time = scraper.cook_time()
            except ScraperExceptions.SchemaOrgException:
                cook_time = None
            
            try:
                prep_time = scraper.prep_time()
            except ScraperExceptions.SchemaOrgException:
                prep_time = None

            try:
                total_time = scraper.total_time()
            except ScraperExceptions.SchemaOrgException:
                total_time = None
            try:
                servings = scraper.yields()
            except ScraperExceptions.SchemaOrgException:
                servings = None

            # --- 2. FASE DE VALIDACIÓN (Estricta con campos obligatorios) ---
            missing_fields = []
            if not title:
                missing_fields.append("título")
            if not image_url:
                missing_fields.append("imagen")
            if not ingredients:
                missing_fields.append("ingredientes")
            if not directions:
                missing_fields.append("pasos")

            if missing_fields:
                error_message = f"Datos obligatorios faltantes: {', '.join(missing_fields)}."
                print(f"Servicio de Scraping: {error_message}")
                raise ValueError(error_message)

            scraped_data = {
                "title": title,
                "image_url": image_url,
                "servings": servings,
                "time": {
                    "cookTime": cook_time,
                    "prepTime": prep_time,
                    "totalTime": total_time,
                },
                "ingredients": ingredients,
                "directions": directions,
                "url": url,
            }

            print(f"Servicio de Scraping: Éxito para: {scraped_data.get('title')}")
            return scraped_data

        except httpx.RequestError as http_err:
            print(f"Servicio de Scraping: Error de red en {url}: {http_err}")
            raise ConnectionError(f"No se pudo acceder a la URL: {http_err}") from http_err
        
        except (ScraperExceptions.WebsiteNotImplementedError, ScraperExceptions.NoSchemaFoundInWildMode) as scrape_err:
            error_type = type(scrape_err).__name__
            print(f"Servicio de Scraping: Error de scraping ({error_type}) en {url}: {scrape_err}")
            raise ValueError(f"El sitio web no es compatible o no se encontraron datos de receta ({error_type})") from scrape_err
        
        except ValueError as val_err:
            # Re-lanzar la excepción de nuestra validación de campos obligatorios
            raise
        
        except Exception as e:
            # Captura cualquier otro error inesperado que no hayamos previsto
            error_type = type(e).__name__
            print(f"Servicio de Scraping: Error inesperado en {url}: ({error_type}) {e}")
            raise RuntimeError(f"Ocurrió un error inesperado durante el scraping: {e}") from e

# Instancia única del servicio
scraping_service = ScrapingService()