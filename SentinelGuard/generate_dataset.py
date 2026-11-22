from pathlib import Path
import numpy as np
import pandas as pd

def generate_dataset(path, rows=12000, seed=42):
    rng = np.random.default_rng(seed)
    amount = np.clip(rng.lognormal(mean=7.2, sigma=1.05, size=rows), 20, 250000)
    hour = rng.integers(0, 24, rows)
    distance = np.clip(rng.gamma(shape=1.6, scale=18, size=rows), 0, 1500)
    new_device = rng.binomial(1, 0.12, rows)
    failed = np.clip(rng.poisson(0.18, rows), 0, 8)
    txns = np.clip(rng.poisson(1.2, rows), 0, 15)
    merchant_risk = rng.beta(2, 7, rows)
    international = rng.binomial(1, 0.07, rows)

    # Synthetic teaching labels: correlated with suspicious signals.
    logit = (
        -5.0
        + 0.000018 * amount
        + 0.0018 * distance
        + 1.45 * new_device
        + 0.48 * failed
        + 0.20 * txns
        + 2.2 * merchant_risk
        + 1.45 * international
        + 0.45 * ((hour <= 4) | (hour >= 23)).astype(float)
    )
    probability = 1 / (1 + np.exp(-logit))
    fraud = rng.binomial(1, probability)
    df = pd.DataFrame({
        "amount": amount.round(2), "hour": hour,
        "distance_from_home_km": distance.round(2),
        "is_new_device": new_device, "failed_attempts_24h": failed,
        "txns_last_hour": txns, "merchant_risk": merchant_risk.round(3),
        "is_international": international, "is_fraud": fraud
    })
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return df

if __name__ == "__main__":
    output = Path(__file__).resolve().parent / "dataset" / "transactions.csv"
    df = generate_dataset(output)
    print(f"Generated {len(df)} synthetic transactions at {output}")
    print(df["is_fraud"].value_counts(normalize=True).rename("class proportion"))
