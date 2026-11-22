from pathlib import Path
import numpy as np
import pandas as pd

FEATURES = ["amount", "hour", "distance_from_home", "merchant_risk",
            "transaction_velocity", "is_foreign", "device_changed"]
TARGET = "is_fraud"

def generate_synthetic_data(n=12000, seed=42):
    # Synthetic development data only; not representative of real bank fraud rates.
    rng = np.random.default_rng(seed)
    amount = rng.lognormal(5.0, 1.15, n).clip(1, 100000)
    hour = rng.integers(0, 24, n)
    distance = rng.gamma(2.0, 35.0, n).clip(0, 1500)
    merchant = rng.beta(2, 5, n)
    velocity = rng.poisson(1.5, n)
    foreign = rng.binomial(1, 0.08, n)
    device = rng.binomial(1, 0.07, n)
    logit = (-5.0 + 0.000025*amount + 0.055*distance + 2.3*merchant
             + 0.25*velocity + 1.4*foreign + 1.7*device
             + 0.8*((hour <= 4) | (hour >= 23)))
    probability = 1 / (1 + np.exp(-logit))
    fraud = rng.binomial(1, probability)
    return pd.DataFrame({"amount": amount.round(2), "hour": hour,
        "distance_from_home": distance.round(2), "merchant_risk": merchant.round(4),
        "transaction_velocity": velocity, "is_foreign": foreign,
        "device_changed": device, "is_fraud": fraud})

def load_dataset(path="data/transactions.csv"):
    p = Path(path)
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        df = generate_synthetic_data()
        df.to_csv(p, index=False)
        return df
    df = pd.read_csv(p)
    required = FEATURES + [TARGET]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")
    df = df[required].apply(pd.to_numeric, errors="coerce").dropna()
    if not set(df[TARGET].unique()).issubset({0, 1}):
        raise ValueError("is_fraud must contain only 0 and 1")
    return df
