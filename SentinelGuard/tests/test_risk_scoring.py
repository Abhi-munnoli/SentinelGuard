from src.risk_scoring.scorer import score_risk

def test_risk_bands():
    assert score_risk(0.2)["risk_level"] == "Low"
    assert score_risk(0.5)["risk_level"] == "Medium"
    assert score_risk(0.9)["risk_level"] == "High"
