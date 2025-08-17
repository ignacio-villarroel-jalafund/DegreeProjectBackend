import os
import pickle
import pandas as pd
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from surprise import Dataset, Reader, SVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.repositories.favorite_repository import favorite_repository
from app.repositories.recipe_repository import recipe_repository
from app.models.recipe import Recipe
from app.core.config import settings

class RecommendationService:
    def __init__(self, favorite_repo, recipe_repo):
        self.favorite_repo = favorite_repo
        self.recipe_repo = recipe_repo
        self.model_dir = settings.MODEL_STORAGE_PATH
        self.model_path = os.path.join(self.model_dir, "recommendation_model.pkl")
        self.backup_model_path = os.path.join(self.model_dir, "recommendation_model_backup.pkl")

        os.makedirs(self.model_dir, exist_ok=True)
        self.model = self._load_latest_model()

    def _load_latest_model(self):
        model_to_load = None
        if os.path.exists(self.model_path):
            model_to_load = self.model_path
            print(f"Loading production model from: {model_to_load}")
        elif os.path.exists(self.backup_model_path):
            model_to_load = self.backup_model_path
            print(f"Loading backup model from: {model_to_load}")

        if model_to_load:
            try:
                with open(model_to_load, "rb") as f:
                    return pickle.load(f)
            except (pickle.UnpicklingError, EOFError, Exception) as e:
                print(f"Error loading model from {model_to_load}: {e}. The file might be corrupted.")

        print("No trained collaborative model found.")
        return None

    def _get_training_data(self, db: Session) -> Optional[pd.DataFrame]:
        all_favorites = self.favorite_repo.get_multi(db, limit=100000)
        if not all_favorites:
            return None
        data = [{"user_id": str(fav.user_id), "recipe_id": str(fav.recipe_id), "rating": 1} for fav in all_favorites]
        return pd.DataFrame(data)

    def train_and_save_model(self, db: Session):
        print("Starting collaborative model training process...")
        df = self._get_training_data(db)
        if df is None or len(df) < 10:
            print("Not enough data to train the model. Aborting.")
            return

        reader = Reader(rating_scale=(0, 1))
        data = Dataset.load_from_df(df[['user_id', 'recipe_id', 'rating']], reader)
        trainset = data.build_full_trainset()

        new_model = SVD(n_factors=100, n_epochs=30, random_state=42)
        print("Training new SVD model...")
        new_model.fit(trainset)
        print("Training complete!")

        if os.path.exists(self.model_path):
            print(f"Backing up current model to: {self.backup_model_path}")
            if os.path.exists(self.backup_model_path):
                os.remove(self.backup_model_path)
            os.rename(self.model_path, self.backup_model_path)

        print(f"Saving new model to: {self.model_path}")
        with open(self.model_path, "wb") as f:
            pickle.dump(new_model, f)

        self.model = new_model
        print("Model training and saving process finished.")

    def _get_content_based_recommendations(self, user_favorite_recipes: List[Recipe], all_recipes: List[Recipe], n_recs: int) -> List[Recipe]:
        print("HYBRID: Generating content-based recommendations.")
        
        def clean_text(text):
            if not isinstance(text, str):
                return ""
            return text.replace("\n", " ").lower()

        recipe_docs = {str(recipe.id): clean_text(recipe.ingredients) for recipe in all_recipes}
        valid_recipe_docs = {rid: ingredients for rid, ingredients in recipe_docs.items() if ingredients}
        
        if not valid_recipe_docs:
            print("Content-based: No recipes with valid ingredients found.")
            return []

        recipe_df = pd.DataFrame(list(valid_recipe_docs.items()), columns=['id', 'ingredients'])
        
        if recipe_df.empty or not user_favorite_recipes:
            print("Content-based: DataFrame is empty or user has no favorites.")
            return []

        tfidf = TfidfVectorizer()
        tfidf_matrix = tfidf.fit_transform(recipe_df['ingredients'])
        
        indices = pd.Series(recipe_df.index, index=recipe_df['id']).drop_duplicates()
        favorite_indices = [indices[str(fav.id)] for fav in user_favorite_recipes if str(fav.id) in indices]

        if not favorite_indices:
            print("Content-based: None of the user's favorites are in the valid recipe set.")
            return []
            
        user_profile_matrix = tfidf_matrix[favorite_indices].mean(axis=0)
        
        user_profile = np.asarray(user_profile_matrix)
        
        sim_scores_to_profile = cosine_similarity(user_profile, tfidf_matrix)
        
        sim_scores_list = sorted(list(enumerate(sim_scores_to_profile[0])), key=lambda x: x[1], reverse=True)
        
        recommended_recipes = []
        user_favorite_ids = {str(fav.id) for fav in user_favorite_recipes}
        recipe_map = {str(r.id): r for r in all_recipes}

        for i, score in sim_scores_list:
            if len(recommended_recipes) >= n_recs:
                break
            recipe_id = recipe_df['id'].iloc[i]
            if recipe_id not in user_favorite_ids:
                recipe_obj = recipe_map.get(recipe_id)
                if recipe_obj:
                    recommended_recipes.append(recipe_obj)
                    
        return recommended_recipes

    def get_recommendations_for_user(self, db: Session, user_id: UUID, n_recs: int = 10) -> List[Recipe]:
        user_id_str = str(user_id)
        user_favorites_assoc = self.favorite_repo.get_user_favorites(db, user_id=user_id, limit=2000)
        user_favorite_recipes = [fav.recipe for fav in user_favorites_assoc if fav.recipe]

        all_recipes = self.recipe_repo.get_multi(db, limit=5000)
        
        content_recs = self._get_content_based_recommendations(user_favorite_recipes, all_recipes, n_recs)
        print(f"Generated {len(content_recs)} content-based recommendations.")
        
        collaborative_recs = []
        if self.model and user_favorite_recipes:
            try:
                user_favorite_ids = {str(r.id) for r in user_favorite_recipes}
                recipes_to_predict = [r for r in all_recipes if str(r.id) not in user_favorite_ids]
                
                predictions = [(r, self.model.predict(uid=user_id_str, iid=str(r.id)).est) for r in recipes_to_predict]
                predictions.sort(key=lambda x: x[1], reverse=True)
                collaborative_recs = [recipe for recipe, score in predictions[:n_recs]]
                print(f"Generated {len(collaborative_recs)} collaborative recommendations.")
            except Exception as e:
                print(f"Could not generate collaborative recommendations: {e}")

        final_recs_map = {}
        for rec in content_recs:
            if rec.id not in final_recs_map:
                final_recs_map[rec.id] = rec
        
        for rec in collaborative_recs:
            if len(final_recs_map) >= n_recs:
                break
            if rec.id not in final_recs_map:
                final_recs_map[rec.id] = rec

        final_recs = list(final_recs_map.values())
        print(f"Returning {len(final_recs)} final hybrid recommendations.")
        return final_recs


recommendation_service = RecommendationService(favorite_repository, recipe_repository)