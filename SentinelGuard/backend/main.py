
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List

from backend.database import SessionLocal, Transaction
from src.preprocessing.validation import validate_transaction
from src.prediction.engine import predict_one

app = FastAPI(
    title="SentinelGuard API",
    version="1.0.0"
)


# -----------------------------
# Transaction Input Validation
# -----------------------------

class TransactionInput(BaseModel):
    amount: float = Field(ge=0)
    hour: int = Field(ge=0, le=23)
    distance_from_home: float = Field(ge=0)
    merchant_risk: float = Field(ge=0, le=1)
    transaction_velocity: int = Field(ge=0)
    is_foreign: int = Field(ge=0, le=1)
    device_changed: int = Field(ge=0, le=1)


# -----------------------------
# Database Connection
# -----------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------
# Format Explanation
# -----------------------------

def format_explanation(explanation, data):
    """
    Convert explanation objects into readable
    feature, value and reason records.
    """

    if isinstance(explanation, dict):
        explanation = [
            {"feature": key, "value": value}
            for key, value in explanation.items()
        ]

    if not isinstance(explanation, list):
        return [{
            "feature": "General",
            "value": "",
            "explanation": str(explanation)
        }]

    formatted = []

    descriptions = {
        "amount": "Transaction amount",
        "hour": "Transaction time",
        "distance_from_home": "Distance from home",
        "merchant_risk": "Merchant risk",
        "transaction_velocity": "Recent transaction count",
        "is_foreign": "Foreign transaction",
        "device_changed": "New device"
    }

    for item in explanation:

        if not isinstance(item, dict):
            formatted.append({
                "feature": "General",
                "value": "",
                "explanation": str(item)
            })
            continue

        feature = item.get(
            "feature",
            item.get("name", item.get("column", "Feature"))
        )

        value = item.get(
            "value",
            item.get("feature_value", data.get(feature, ""))
        )

        reason = item.get(
            "explanation",
            item.get(
                "description",
                item.get("reason", item.get("impact", ""))
            )
        )

        if isinstance(value, (dict, list)):
            value = str(value)

        if isinstance(reason, (dict, list)):
            reason = str(reason)

        feature_name = descriptions.get(
            str(feature),
            str(feature).replace("_", " ").title()
        )

        if not reason:
            reason = f"Model explanation for {feature_name}"

        formatted.append({
            "feature": feature_name,
            "value": value,
            "explanation": str(reason)
        })

    return formatted


# -----------------------------
# Health Check
# -----------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "SentinelGuard"
    }


# -----------------------------
# Process Transaction
# -----------------------------

def process(data, db):

    try:
        clean = validate_transaction(data)
        result = predict_one(clean)

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc)
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc)
        )

    explanation = format_explanation(
        result.get("explanation", []),
        clean
    )

    record = Transaction(
        **clean,
        fraud_probability=result["fraud_probability"],
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        prediction=result["prediction"],
        explanation=explanation
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "transaction_id": record.id,
        "fraud_probability": result["fraud_probability"],
        "risk_score": result["risk_score"],
        "risk_level": result["risk_level"],
        "prediction": result["prediction"],
        "explanation": explanation
    }


# -----------------------------
# Single Transaction Prediction
# -----------------------------

@app.post("/predict")
def predict(
    payload: TransactionInput,
    db: Session = Depends(get_db)
):
    return process(payload.model_dump(), db)


# -----------------------------
# Batch Transaction Prediction
# -----------------------------

@app.post("/predict/batch")
def predict_batch(
    payload: List[TransactionInput],
    db: Session = Depends(get_db)
):

    if len(payload) > 500:
        raise HTTPException(
            status_code=413,
            detail="Maximum batch size is 500"
        )

    return [
        process(item.model_dump(), db)
        for item in payload
    ]


# -----------------------------
# Transaction History
# -----------------------------

@app.get("/transactions")
def transactions(
    limit: int = 100,
    db: Session = Depends(get_db)
):

    rows = (
        db.query(Transaction)
        .order_by(desc(Transaction.id))
        .limit(max(1, min(limit, 1000)))
        .all()
    )

    return [
        {
            "id": r.id,
            "created_at": r.created_at.isoformat(),
            "amount": r.amount,
            "fraud_probability": r.fraud_probability,
            "risk_score": r.risk_score,
            "risk_level": r.risk_level,
            "prediction": r.prediction,
            "explanation": r.explanation
        }
        for r in rows
    ]


# -----------------------------
# Dashboard Metrics
# -----------------------------

@app.get("/metrics")
def metrics(db: Session = Depends(get_db)):

    rows = db.query(Transaction).all()

    total = len(rows)
    fraud = sum(r.prediction for r in rows)
    high = sum(r.risk_level == "High" for r in rows)

    return {
        "total_transactions": total,
        "predicted_fraud": fraud,
        "legitimate": total - fraud,
        "high_risk": high,
        "fraud_rate": round(
            fraud / total * 100, 2
        ) if total else 0
    }
