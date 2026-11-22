from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split

FEATURES = [
    "amount", "hour", "distance_from_home_km", "is_new_device",
    "failed_attempts_24h", "txns_last_hour", "merchant_risk", "is_international"
]

class FraudModel:
    def __init__(self, model_path):
        self.model_path = model_path
        self.bundle = None
        if Path(model_path).exists():
            self.bundle = joblib.load(model_path)

    @property
    def is_ready(self):
        return self.bundle is not None

    def train_and_save(self, dataset_path):
        from generate_dataset import generate_dataset
        path = Path(dataset_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            generate_dataset(path, rows=12000, seed=42)
        df = pd.read_csv(path)
        X = df[FEATURES]
        y = df["is_fraud"].astype(int)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        model = RandomForestClassifier(
            n_estimators=180, max_depth=12, min_samples_leaf=2,
            class_weight="balanced_subsample", random_state=42, n_jobs=-1
        )
        model.fit(X_train, y_train)
        probabilities = model.predict_proba(X_test)[:, 1]
        predictions = (probabilities >= 0.5).astype(int)
        metrics = {
            "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
            "precision": round(float(precision_score(y_test, predictions, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, predictions, zero_division=0)), 4),
            "f1": round(float(f1_score(y_test, predictions, zero_division=0)), 4),
            "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
        }
        self.bundle = {
            "model": model, "features": FEATURES,
            "metrics": metrics, "training_rows": int(len(df))
        }
        Path(self.model_path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.bundle, self.model_path)
        return metrics

    def predict(self, transaction):
        if not self.is_ready:
            raise RuntimeError("Model is not trained. Run python train_model.py.")
        row = pd.DataFrame([{key: transaction[key] for key in FEATURES}], columns=FEATURES)
        probability = float(self.bundle["model"].predict_proba(row)[0, 1])
        risk = int(round(probability * 100))
        label = "Fraud" if probability >= 0.5 else "Genuine"
        level = "High" if risk >= 70 else ("Medium" if risk >= 35 else "Low")
        reasons = self._explain(row)
        return {
            "prediction": label,
            "fraud_probability": round(probability, 4),
            "risk_score": risk,
            "risk_level": level,
            "explanation": reasons,
            "model_version": "RandomForest-v1"
        }

    def _explain(self, row):
        model = self.bundle["model"]
        importances = model.feature_importances_
        values = row.iloc[0]
        # Transparent local explanation: highlights influential inputs that are unusual
        # relative to typical transaction values in this demonstration dataset.
        medians = {
            "amount": 1800, "hour": 14, "distance_from_home_km": 12,
            "is_new_device": 0, "failed_attempts_24h": 0, "txns_last_hour": 1,
            "merchant_risk": 0.2, "is_international": 0
        }
        labels = {
            "amount": "Transaction amount",
            "hour": "Transaction time",
            "distance_from_home_km": "Distance from usual location",
            "is_new_device": "New device",
            "failed_attempts_24h": "Failed attempts",
            "txns_last_hour": "Transaction frequency",
            "merchant_risk": "Merchant risk",
            "is_international": "International transaction"
        }
        scored = []
        for feature, importance in zip(FEATURES, importances):
            val = float(values[feature])
            baseline = medians[feature]
            unusual = abs(val - baseline) / (abs(baseline) + 1)
            if feature in ("is_new_device", "is_international", "failed_attempts_24h"):
                unusual = val
            scored.append((float(importance) * (1 + min(unusual, 10)), labels[feature], val))
        scored.sort(reverse=True)
        return [
            f"{name}: {value:g} (model-relevant input)"
            for _, name, value in scored[:3]
        ]
