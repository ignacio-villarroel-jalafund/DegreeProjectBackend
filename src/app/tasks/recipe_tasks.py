from typing import Dict, Any

from app.celery.celery_app import celery_app
from app.services import nutrition_service
from app.services.analysis_service import analysis_service
from app.services.scraping_service import scraping_service
from app.services.recipe_processor_service import recipe_processor_service

@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
async def scrape_and_analyze_recipe(self, url: str) -> Dict[str, Any]:
    task_id = self.request.id

    try:
        scraped_data = await scraping_service.scrape_recipe_from_url(url)
        cleaned_data = recipe_processor_service.process(scraped_data)

        if cleaned_data and cleaned_data.get('ingredients'):
            print(f"[{task_id}] Calculating nutritional information...")
            nutritional_info = await nutrition_service.calculate_nutritional_info_for_recipe(
                ingredients=cleaned_data['ingredients']
            )
            cleaned_data['nutrition'] = nutritional_info
            print(f"[{task_id}] Nutritional information calculated.")
        
        return cleaned_data

    except (ValueError, ConnectionError, RuntimeError) as exc:
        message = f"Scraping phase failed: {exc}"
        print(f"[{task_id}] {message}")
        self.update_state(state='FAILURE', meta={'exc_type': type(exc).__name__, 'exc_message': str(exc)})
        return {"status": "FAILURE", "message": message}


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def analyze_and_return(self, scraped_data_dict: Dict[str, Any]) -> Dict[str, Any]:
    task_id = self.request.id
    recipe_name = scraped_data_dict.get("recipe_name", "Unknown Name")
    print(f"[{task_id}] Starting ANALYSIS for recipe: {recipe_name}")

    if not recipe_name:
        message = "Incomplete scraped data (recipe_name)."
        print(f"[{task_id}] {message}")
        self.update_state(state='FAILURE', meta={'exc_type': 'ValueError', 'exc_message': message})
        return {"status": "FAILURE", "message": message}

    try:
        print(f"[{task_id}] Analyzing recipe...")
        analysis_text = analysis_service.analyze_recipe(scraped_data_dict)
        status = "SUCCESS"
        message = f"Analysis completed for {recipe_name}."
        print(f"[{task_id}] Analysis finished.")
    except Exception as exc:
        status = "FAILURE"
        analysis_text = None
        message = f"Error during analysis: {exc}"
        print(f"[{task_id}] {message}")
        self.update_state(state='FAILURE', meta={'exc_type': type(exc).__name__, 'exc_message': str(exc)})

    return {
        "status": status,
        "analysis": analysis_text,
        "message": message
    }