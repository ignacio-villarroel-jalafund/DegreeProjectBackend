import sys
import os
import asyncio
import json
from uuid import uuid4
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.recipe import Recipe
from app.models.favorite import Favorite
from app.core.security import get_password_hash

from app.services.scraping_service import scraping_service
from app.services.recipe_processor_service import recipe_processor_service
from app.services.nutrition_service import nutrition_service

CACHE_FILE = 'scraped_data_cache.json'

RECIPES_BY_CATEGORY = {
    "Vegano": ["https://cookpad.com/bo/recetas/17219292", "https://cookpad.com/bo/recetas/24647195", "https://cookpad.com/bo/recetas/24629062", "https://cookpad.com/bo/recetas/24615505", "https://cookpad.com/bo/recetas/24585807", "https://cookpad.com/bo/recetas/24431246", "https://cookpad.com/bo/recetas/24416605", "https://cookpad.com/bo/recetas/24392020", "https://cookpad.com/bo/recetas/24543271", "https://cookpad.com/bo/recetas/23928273", "https://cookpad.com/bo/recetas/24425336"],
    "Sin lactosa": ["https://cookpad.com/bo/recetas/24059393", "https://cookpad.com/bo/recetas/24056577", "https://cookpad.com/bo/recetas/23986956", "https://cookpad.com/bo/recetas/23888604", "https://cookpad.com/bo/recetas/17286683", "https://cookpad.com/bo/recetas/24425336", "https://cookpad.com/bo/recetas/16742733"],
    "Sin gluten": ["https://cookpad.com/bo/recetas/15058582", "https://cookpad.com/bo/recetas/24927216", "https://cookpad.com/bo/recetas/24897116", "https://cookpad.com/bo/recetas/24892487", "https://cookpad.com/bo/recetas/24858991", "https://cookpad.com/bo/recetas/24848623", "https://cookpad.com/bo/recetas/24425336", "https://cookpad.com/bo/recetas/16742733", "https://cookpad.com/bo/recetas/24590852", "https://cookpad.com/bo/recetas/24023016", "https://cookpad.com/bo/recetas/24173731"],
    "Carne": ["https://cookpad.com/bo/recetas/24542473", "https://cookpad.com/bo/recetas/3588160", "https://cookpad.com/bo/recetas/12648374", "https://cookpad.com/bo/recetas/14830480", "https://cookpad.com/bo/recetas/11935466", "https://cookpad.com/bo/recetas/5347836", "https://cookpad.com/bo/recetas/24281420", "https://cookpad.com/bo/recetas/24919652", "https://cookpad.com/bo/recetas/24859762", "https://cookpad.com/bo/recetas/24813789", "https://cookpad.com/bo/recetas/24047926", "https://cookpad.com/bo/recetas/23955305", "https://cookpad.com/bo/recetas/5665434", "https://cookpad.com/bo/recetas/15794865", "https://cookpad.com/bo/recetas/24590852"],
    "Postres": ["https://cookpad.com/bo/recetas/17077636", "https://cookpad.com/bo/recetas/4618990", "https://cookpad.com/bo/recetas/3757119", "https://cookpad.com/bo/recetas/24925547", "https://cookpad.com/bo/recetas/15252107", "https://cookpad.com/bo/recetas/24874947", "https://cookpad.com/bo/recetas/16063100", "https://cookpad.com/bo/recetas/24471926", "https://cookpad.com/bo/recetas/24044048", "https://cookpad.com/bo/recetas/24425336", "https://cookpad.com/bo/recetas/16742733", "https://cookpad.com/bo/recetas/24173731"],
    "Sopas": ["https://cookpad.com/bo/recetas/24916239", "https://cookpad.com/bo/recetas/24851672", "https://cookpad.com/bo/recetas/24833006", "https://cookpad.com/bo/recetas/24803262", "https://cookpad.com/bo/recetas/24197103", "https://cookpad.com/bo/recetas/24813789", "https://cookpad.com/bo/recetas/15794865", "https://cookpad.com/bo/recetas/24663487"],
    "Boliviana": ["https://cookpad.com/bo/recetas/14543371", "https://cookpad.com/bo/recetas/12648374", "https://cookpad.com/bo/recetas/13550372", "https://cookpad.com/bo/recetas/923015", "https://cookpad.com/bo/recetas/11935466", "https://cookpad.com/bo/recetas/23974379", "https://cookpad.com/bo/recetas/108622", "https://cookpad.com/bo/recetas/23955305", "https://cookpad.com/bo/recetas/5665434"],
    "Comida rapida": ["https://cookpad.com/bo/recetas/5347836", "https://cookpad.com/bo/recetas/24710318", "https://cookpad.com/bo/recetas/24281420", "https://cookpad.com/bo/recetas/24543271", "https://cookpad.com/bo/recetas/23928273", "https://cookpad.com/bo/recetas/24919652", "https://cookpad.com/bo/recetas/24859762", "https://cookpad.com/bo/recetas/24848623", "https://cookpad.com/bo/recetas/24813789", "https://cookpad.com/bo/recetas/24047926", "https://cookpad.com/bo/recetas/16063100", "https://cookpad.com/bo/recetas/24471926", "https://cookpad.com/bo/recetas/24044048"]
}

USER_PERSONAS = [
    {"username": "vegan_enthusiast", "email": "vegan_enthusiast@example.com", "likes": ["Vegano"]},
    {"username": "carnivore_king", "email": "carnivore_king@example.com", "likes": ["Carne"]},
    {"username": "dessert_lover", "email": "dessert_lover@example.com", "likes": ["Postres"]},
    {"username": "soup_aficionado", "email": "soup_aficionado@example.com", "likes": ["Sopas"]},
    {"username": "fast_food_fan", "email": "fast_food_fan@example.com", "likes": ["Comida rapida"]},
    {"username": "bolivian_foodie", "email": "bolivian_foodie@example.com", "likes": ["Boliviana"]},
    {"username": "gluten_free_gourmet", "email": "glutenfree@example.com", "likes": ["Sin gluten"]},
    {"username": "lactose_free_life", "email": "lactosefree@example.com", "likes": ["Sin lactosa"]},
    {"username": "comfort_food_cook", "email": "comfort_food@example.com", "likes": ["Sopas", "Carne"]},
    {"username": "patriotic_carnivore", "email": "patriotic_carnivore@example.com", "likes": ["Carne", "Boliviana"]},
    {"username": "sweet_baker_gf", "email": "sweet_baker_gf@example.com", "likes": ["Postres", "Sin gluten"]},
    {"username": "healthy_and_fast", "email": "healthy_fast@example.com", "likes": ["Vegano", "Comida rapida"]},
    {"username": "traditional_soups", "email": "trad_soups@example.com", "likes": ["Sopas", "Boliviana"]},
    {"username": "party_host", "email": "party_host@example.com", "likes": ["Comida rapida", "Postres"]},
    {"username": "allergy_conscious_baker", "email": "allergy_baker@example.com", "likes": ["Postres", "Sin lactosa", "Sin gluten"]},
]

def get_cache_file_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), CACHE_FILE)

def load_cache():
    try:
        with open(get_cache_file_path(), 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_cache(data):
    with open(get_cache_file_path(), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def safe_parse_servings(servings_text: any) -> int:
    if not servings_text: return 1
    try:
        parts = str(servings_text).split(' ')
        for part in parts:
            if part.isdigit(): return int(part)
    except (ValueError, AttributeError): pass
    return 1

async def get_scraped_and_analyzed_data(url: str):
    try:
        scraped_data = await scraping_service.scrape_recipe_from_url(url)
        cleaned_data = recipe_processor_service.process(scraped_data)

        if cleaned_data and cleaned_data.get('ingredients'):
            nutritional_info = await nutrition_service.calculate_nutritional_info_for_recipe(
                ingredients=cleaned_data['ingredients']
            )
            cleaned_data['nutrition'] = nutritional_info.model_dump() if hasattr(nutritional_info, 'model_dump') else vars(nutritional_info)
        
        return cleaned_data
    except Exception as exc:
        print(f"  -> Failed to process URL {url}: {exc}")
        return None

async def seed():
    db: Session = SessionLocal()
    scraped_cache = load_cache()
    
    try:
        url_to_recipe_map = {}
        all_urls = sorted(list(set(url for urls in RECIPES_BY_CATEGORY.values() for url in urls)))
        
        new_data_scraped = False
        for url in all_urls:
            existing_recipe = db.query(Recipe).filter(Recipe.url == str(url)).first()
            if existing_recipe:
                url_to_recipe_map[url] = existing_recipe
                continue
            
            scraped_data = None
            if url in scraped_cache:
                print(f"Using cache for: {url}")
                scraped_data = scraped_cache[url]
            else:
                print(f"Scraping new URL: {url}")
                scraped_data = await get_scraped_and_analyzed_data(url)
                if scraped_data:
                    scraped_cache[url] = scraped_data
                    new_data_scraped = True

            if not scraped_data or not scraped_data.get('title'): 
                print(f"  -> Skipping URL due to missing data or error: {url}")
                continue

            try:
                recipe_obj = Recipe(
                    id=uuid4(),
                    recipe_name=scraped_data.get('title'),
                    servings=safe_parse_servings(scraped_data.get('servings')),
                    ingredients="\n".join(scraped_data.get('ingredients', [])),
                    directions="\n".join(scraped_data.get('directions', [])),
                    nutrition=json.dumps(scraped_data.get('nutrition')) if scraped_data.get('nutrition') else None,
                    url=str(scraped_data.get('url')),
                    img_src=str(scraped_data.get('image_url')) if scraped_data.get('image_url') else None
                )
                db.add(recipe_obj)
                db.commit()
                db.refresh(recipe_obj)
                url_to_recipe_map[url] = recipe_obj

            except Exception as e:
                print(f"  -> Database Error for URL {url}: {e}")
                db.rollback()

        if new_data_scraped:
            save_cache(scraped_cache)

        print("\nCreating users and preparing favorite relations")
        favorites_to_add = set()
        for persona in USER_PERSONAS:
            user_obj = db.query(User).filter(User.email == persona['email']).first()
            if not user_obj:
                print(f"Creating user: {persona['username']}")
                user_obj = User(id=uuid4(), username=persona['username'], email=persona['email'], password=get_password_hash("string"))
                db.add(user_obj)
                db.commit()
                db.refresh(user_obj)
            
            for category in persona['likes']:
                for url in RECIPES_BY_CATEGORY.get(category, []):
                    if url in url_to_recipe_map:
                        recipe = url_to_recipe_map[url]
                        favorites_to_add.add((user_obj.id, recipe.id))
        
        for user_id, recipe_id in favorites_to_add:
            existing_fav = db.query(Favorite).filter_by(user_id=user_id, recipe_id=recipe_id).first()
            if not existing_fav:
                db.add(Favorite(id=uuid4(), user_id=user_id, recipe_id=recipe_id))
        
        db.commit()

    finally:
        db.close()

if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    asyncio.run(seed())