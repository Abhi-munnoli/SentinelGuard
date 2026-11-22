from pathlib import Path
import json, joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix)
from src.preprocessing.data import FEATURES, TARGET, load_dataset

ROOT = Path(__file__).resolve().parents[2]

def main():
    df = load_dataset(str(ROOT / "data" / "transactions.csv"))
    X, y = df[FEATURES], df[TARGET].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)
    model = RandomForestClassifier(n_estimators=250, max_depth=12,
        min_samples_leaf=3, class_weight="balanced_subsample",
        random_state=42, n_jobs=-1)
    # SMOTE is applied only after splitting and only to the training partition.
    try:
        from imblearn.over_sampling import SMOTE
        if y_train.value_counts().min() >= 2:
            X_train, y_train = SMOTE(random_state=42).fit_resample(X_train, y_train)
    except ImportError:
        pass
    model.fit(X_train, y_train)
    pred, prob = model.predict(X_test), model.predict_proba(X_test)[:, 1]
    metrics = {
        "accuracy": float(accuracy_score(y_test, pred)),
        "precision": float(precision_score(y_test, pred, zero_division=0)),
        "recall": float(recall_score(y_test, pred, zero_division=0)),
        "f1": float(f1_score(y_test, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, prob)),
        "average_precision": float(average_precision_score(y_test, prob)),
        "confusion_matrix": confusion_matrix(y_test, pred).tolist(),
        "features": FEATURES, "test_rows": int(len(X_test))}
    (ROOT / "models").mkdir(exist_ok=True)
    (ROOT / "reports").mkdir(exist_ok=True)
    joblib.dump({"model": model, "features": FEATURES}, ROOT / "models/sentinelguard.joblib")
    (ROOT / "reports/metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()
