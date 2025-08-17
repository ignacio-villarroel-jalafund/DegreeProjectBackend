import sys
import os
import pandas as pd
from surprise import Dataset, Reader, SVD
from surprise.model_selection import cross_validate

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.repositories.favorite_repository import favorite_repository

def evaluate():
    print("--- Starting Recommendation Model Evaluation ---")
    db = SessionLocal()
    try:
        print("Step 1: Fetching favorite data...")
        all_favorites = favorite_repository.get_multi(db, limit=100000)
        
        if not all_favorites or len(all_favorites) < 20:
            print("Not enough data to perform a meaningful evaluation.")
            return

        print(f"Found {len(all_favorites)} favorite records.")

        data = [
            {"user_id": str(fav.user_id), "recipe_id": str(fav.recipe_id), "rating": 1}
            for fav in all_favorites
        ]
        df = pd.DataFrame(data)
        
        reader = Reader(rating_scale=(0, 1))
        dataset = Dataset.load_from_df(df[['user_id', 'recipe_id', 'rating']], reader)

        print("\nStep 2: Setting up SVD algorithm for evaluation...")
        algo = SVD(n_factors=100, n_epochs=30, random_state=42)

        print("Step 3: Running cross-validation (this may take a while)...")
        results = cross_validate(algo, dataset, measures=['RMSE', 'MAE'], cv=5, verbose=True)

        print("\n--- Evaluation Results ---")
        mean_rmse = results['test_rmse'].mean()
        mean_mae = results['test_mae'].mean()
        
        print(f"Average RMSE: {mean_rmse:.4f}")
        print(f"Average MAE:  {mean_mae:.4f}")
        print("\nReminder: Lower values indicate better model performance.")

    finally:
        db.close()

if __name__ == "__main__":
    evaluate()
