import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "local-demo-only-change-before-deployment")
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    MODEL_PATH = str(BASE_DIR / "models" / "fraud_model.joblib")
    DATASET_PATH = str(BASE_DIR / "dataset" / "transactions.csv")
    DATABASE_PATH = str(BASE_DIR / "data" / "sentinelguard.db")
    FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS", "serviceAccountKey.json")
    FIRESTORE_COLLECTION = os.getenv("FIRESTORE_COLLECTION", "transactions")
    STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "auto").lower()
