import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.services.recommendation_service import recommendation_service

def main():
    db = SessionLocal()
    try:
        recommendation_service.train_and_save_model(db)
    finally:
        db.close()

if __name__ == "__main__":
    main()
