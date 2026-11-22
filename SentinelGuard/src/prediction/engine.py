from pathlib import Path
import joblib
import pandas as pd
from src.preprocessing.data import FEATURES
from src.risk_scoring.scorer import score_risk
from src.explainability.explainer import explain_prediction

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "models" / "sentinelguard.joblib"
_cached = None

def get_model():
    global _cached
    if _cached is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError("Model not found. Run: python -m src.training.train")
        _cached = joblib.load(MODEL_PATH)
    return _cached["model"]

def predict_one(transaction):
    model = get_model()
    row = pd.DataFrame([{k: transaction[k] for k in FEATURES}], columns=FEATURES)
    probability = float(model.predict_proba(row)[0, 1])
    result = score_risk(probability)
    result.update({"explanation": explain_prediction(model, row),
                   "fraud_probability": round(probability, 6),
                   "prediction": int(probability >= 0.5)})
    return result
