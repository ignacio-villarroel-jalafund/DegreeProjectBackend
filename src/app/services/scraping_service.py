from typing import Dict, Any
from urllib.parse import urlparse

import httpx
from recipe_scrapers import scrape_me, _exceptions as ScraperExceptions

class ScrapingService:

    def _is_valid_url(self, url: str) -> bool:
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except (ValueError, AttributeError):
            return False

    async def scrape_recipe_from_url(self, url: str) -> Dict[str, Any]:
        print(f"Scraping Service: Starting for URL: {url}")

        if not self._is_valid_url(url):
            raise ValueError("The provided URL is not valid.")

        try:
            scraper = scrape_me(url=url)
            
            title = scraper.title()
            image_url = scraper.image()
            ingredients = scraper.ingredients()
            directions = scraper.instructions_list()

            try:
                servings = scraper.yields()
            except ScraperExceptions.SchemaOrgException:
                servings = None

            missing_fields = []
            if not title:
                missing_fields.append("title")
            if not image_url:
                missing_fields.append("image")
            if not ingredients:
                missing_fields.append("ingredients")
            if not directions:
                missing_fields.append("steps")

            if missing_fields:
                error_message = f"Missing mandatory data: {', '.join(missing_fields)}."
                print(f"Scraping Service: {error_message}")
                raise ValueError(error_message)

            scraped_data = {
                "title": title,
                "image_url": image_url,
                "servings": servings,
                "ingredients": ingredients,
                "directions": directions,
                "url": url,
            }

            print(f"Scraping Service: Success for: {scraped_data.get('title')}")
            return scraped_data

        except httpx.RequestError as http_err:
            print(f"Scraping Service: Network error at {url}: {http_err}")
            raise ConnectionError(f"Could not access the URL: {http_err}") from http_err
        
        except (ScraperExceptions.WebsiteNotImplementedError, ScraperExceptions.NoSchemaFoundInWildMode) as scrape_err:
            error_type = type(scrape_err).__name__
            print(f"Scraping Service: Scraping error ({error_type}) at {url}: {scrape_err}")
            raise ValueError(f"The website is not supported or no recipe data was found ({error_type})") from scrape_err
        
        except ValueError as val_err:
            raise
        
        except Exception as e:
            error_type = type(e).__name__
            print(f"Scraping Service: Unexpected error at {url}: ({error_type}) {e}")
            raise RuntimeError(f"An unexpected error occurred during scraping: {e}") from e

scraping_service = ScrapingService()
