# SentinelGuard
Real-time banking fraud intelligence and explainable risk scoring demo.

## Quick start (Python 3.10+)
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m src.training.train
uvicorn backend.main:app --reload
```
In another terminal run `streamlit run frontend/app.py`.
API docs: http://127.0.0.1:8000/docs | Dashboard: http://localhost:8501

If `data/transactions.csv` is absent, training creates a reproducible synthetic dataset.
For your own CSV, use the columns in `data/sample_transactions.csv`. The target is `is_fraud` (0/1).

## Features
- Random Forest fraud classifier, optional SMOTE on training split only
- Risk score and Low/Medium/High classification
- Optional SHAP explanations with safe feature-importance fallback
- FastAPI prediction, batch, history and metrics endpoints
- Streamlit dashboard, transaction history and CSV export
- SQLite persistence; optional Kafka consumer extension

## Input fields
`amount`, `hour` (0-23), `distance_from_home`, `merchant_risk` (0-1),
`transaction_velocity`, `is_foreign` (0/1), `device_changed` (0/1).

## Important
This is an educational prototype, not a production banking system. Add authentication,
authorization, encryption, secrets management, rate limiting, audit logging, drift monitoring
and human review before real deployment. A risk score is a decision-support signal, not proof of fraud.
