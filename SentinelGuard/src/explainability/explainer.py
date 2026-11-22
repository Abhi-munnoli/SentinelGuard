def explain_prediction(model, row):
    # Prefer SHAP local attributions; fall back to global feature importance.
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        values = explainer.shap_values(row)
        if isinstance(values, list):
            vals = values[1][0]
        else:
            vals = values[0]
            if getattr(vals, "ndim", 1) == 2:
                vals = vals[:, 1] if vals.shape[1] > 1 else vals[:, 0]
        pairs = sorted(zip(row.columns, vals), key=lambda x: abs(float(x[1])), reverse=True)
        return [{"feature": str(k), "impact": round(float(v), 5)} for k, v in pairs[:5]]
    except Exception:
        if hasattr(model, "feature_importances_"):
            pairs = sorted(zip(row.columns, model.feature_importances_),
                           key=lambda x: float(x[1]), reverse=True)
            return [{"feature": str(k), "impact": round(float(v), 5),
                     "note": "Global importance, not a local causal explanation"}
                    for k, v in pairs[:5]]
        return [{"feature": "explanation", "impact": 0.0, "note": "SHAP unavailable"}]
