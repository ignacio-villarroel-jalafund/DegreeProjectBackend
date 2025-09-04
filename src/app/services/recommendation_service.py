import os
import pickle
import random
import pandas as pd
from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy.orm import Session
from surprise import Dataset, Reader, SVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import numpy as np

from app.repositories.favorite_repository import favorite_repository
from app.repositories.recipe_repository import recipe_repository
from app.models.recipe import Recipe
from app.core.config import settings
from app.schemas.recommendation import Recommendation


class RecommendationService:
    def __init__(self, favorite_repo, recipe_repo):
        self.favorite_repo = favorite_repo
        self.recipe_repo = recipe_repo
        self.model_dir = settings.MODEL_STORAGE_PATH
        self.model_path = os.path.join(
            self.model_dir, "recommendation_model.pkl")
        self.backup_model_path = os.path.join(
            self.model_dir, "recommendation_model_backup.pkl")

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
                print(
                    f"Error loading model from {model_to_load}: {e}. The file might be corrupted.")

        print("No trained collaborative model found.")
        return None

    def _get_training_data(self, db: Session) -> Optional[pd.DataFrame]:
        all_favorites = self.favorite_repo.get_multi(db, limit=100000)
        if not all_favorites:
            return None
        data = [{"user_id": str(fav.user_id), "recipe_id": str(
            fav.recipe_id), "rating": 1} for fav in all_favorites]
        return pd.DataFrame(data)

    def train_and_save_model(self, db: Session):
        df = self._get_training_data(db)
        if df is None or len(df) < 10:
            print("Not enough data to train the model. Aborting.")
            return

        reader = Reader(rating_scale=(0, 1))
        data = Dataset.load_from_df(
            df[['user_id', 'recipe_id', 'rating']], reader)
        trainset = data.build_full_trainset()

        new_model = SVD(n_factors=100, n_epochs=30, random_state=42)
        print("Training new SVD model")
        new_model.fit(trainset)

        if os.path.exists(self.model_path):
            if os.path.exists(self.backup_model_path):
                os.remove(self.backup_model_path)
            os.rename(self.model_path, self.backup_model_path)

        with open(self.model_path, "wb") as f:
            pickle.dump(new_model, f)

        self.model = new_model

    def _get_content_based_recommendations(self, user_favorite_recipes: List[Recipe], all_recipes: List[Recipe], n_recs: int) -> List[Dict]:

        if not user_favorite_recipes:
            return []

        def clean_text(text):
            if not isinstance(text, str):
                return ""
            return text.replace("\n", " ").lower()

        recipe_docs = {str(recipe.id): clean_text(
            f"{recipe.recipe_name} {recipe.ingredients}") for recipe in all_recipes}
        recipe_map = {str(r.id): r for r in all_recipes}
        user_favorite_ids = {str(fav.id) for fav in user_favorite_recipes}

        recipe_df = pd.DataFrame(list(recipe_docs.items()), columns=[
                                 'id', 'content'])
        indices = pd.Series(recipe_df.index,
                            index=recipe_df['id']).drop_duplicates()

        tfidf = TfidfVectorizer()
        tfidf_matrix = tfidf.fit_transform(recipe_df['content'])

        recommendations = {}

        for fav_recipe in user_favorite_recipes:
            fav_recipe_id_str = str(fav_recipe.id)
            if fav_recipe_id_str not in indices:
                continue

            idx = indices[fav_recipe_id_str]
            cosine_similarities = linear_kernel(
                tfidf_matrix[idx:idx+1], tfidf_matrix).flatten()
            related_docs_indices = cosine_similarities.argsort()[:-10:-1]

            for i in related_docs_indices:
                recommended_recipe_id = recipe_df['id'][i]
                if recommended_recipe_id != fav_recipe_id_str and recommended_recipe_id not in user_favorite_ids:
                    if recommended_recipe_id not in recommendations:
                        recommendations[recommended_recipe_id] = {
                            "recipe": recipe_map[recommended_recipe_id],
                            "reason": f"Porque te gustó \"{fav_recipe.recipe_name}\"",
                            "score": cosine_similarities[i]
                        }

        sorted_recs = sorted(
            recommendations.values(), key=lambda x: x["score"], reverse=True)
        return sorted_recs[:n_recs]

    def get_recommendations_for_user(self, db: Session, user_id: UUID, n_recs: int = 10) -> List[Recommendation]:
        user_id_str = str(user_id)
        user_favorites_assoc = self.favorite_repo.get_user_favorites(
            db, user_id=user_id, limit=2000)
        user_favorite_recipes = [
            fav.recipe for fav in user_favorites_assoc if fav.recipe]

        if not user_favorite_recipes:
            return []
            
        all_recipes = self.recipe_repo.get_multi(db, limit=5000)

        content_recs_data = self._get_content_based_recommendations(
            user_favorite_recipes, all_recipes, n_recs)

        collaborative_recs_data = []
        if self.model:
            try:
                user_favorite_ids = {str(r.id) for r in user_favorite_recipes}
                recipes_to_predict = [
                    r for r in all_recipes if str(r.id) not in user_favorite_ids]

                predictions = [(r, self.model.predict(
                    uid=user_id_str, iid=str(r.id)).est) for r in recipes_to_predict]
                predictions.sort(key=lambda x: x[1], reverse=True)

                most_recent_favorite = user_favorite_recipes[0]

                for recipe, score in predictions[:n_recs]:
                    collaborative_recs_data.append({
                        "recipe": recipe,
                        "reason": f"A otros usuarios que les gustó \"{most_recent_favorite.recipe_name}\" también les gustó esto"
                    })

                print(
                    f"Generated {len(collaborative_recs_data)} collaborative recommendations.")
            except Exception as e:
                print(f"Could not generate collaborative recommendations: {e}")
        
        final_recs_map = {}
        
        for rec_data in content_recs_data:
            rec_id = rec_data["recipe"].id
            if rec_id not in final_recs_map:
                final_recs_map[rec_id] = Recommendation(
                    recipe=rec_data["recipe"],
                    reason=rec_data["reason"]
                )
        
        for rec_data in collaborative_recs_data:
            if len(final_recs_map) >= n_recs:
                break
            rec_id = rec_data["recipe"].id
            if rec_id not in final_recs_map:
                final_recs_map[rec_id] = Recommendation(
                    recipe=rec_data["recipe"],
                    reason=rec_data["reason"]
                )

        final_recs = list(final_recs_map.values())
        random.shuffle(final_recs)

        return final_recs


recommendation_service = RecommendationService(
    favorite_repository, recipe_repository)