def score_risk(probability):
    probability = max(0.0, min(1.0, float(probability)))
    score = round(probability * 100, 1)
    level = "Low" if score <= 30 else "Medium" if score <= 70 else "High"
    return {"risk_score": score, "risk_level": level}
