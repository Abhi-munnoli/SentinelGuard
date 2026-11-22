from src.preprocessing.data import FEATURES

def validate_transaction(data):
    cleaned = {}
    for name in FEATURES:
        if name not in data:
            raise ValueError(f"Missing field: {name}")
        cleaned[name] = float(data[name])
    if cleaned["amount"] < 0: raise ValueError("amount cannot be negative")
    if not 0 <= cleaned["hour"] <= 23: raise ValueError("hour must be between 0 and 23")
    if cleaned["distance_from_home"] < 0: raise ValueError("distance cannot be negative")
    if not 0 <= cleaned["merchant_risk"] <= 1: raise ValueError("merchant_risk must be between 0 and 1")
    if cleaned["transaction_velocity"] < 0: raise ValueError("velocity cannot be negative")
    for key in ("is_foreign", "device_changed"):
        if cleaned[key] not in (0, 1): raise ValueError(f"{key} must be 0 or 1")
        cleaned[key] = int(cleaned[key])
    cleaned["hour"] = int(cleaned["hour"])
    return cleaned
