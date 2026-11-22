import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from config import Config
from model_service import FraudModel
from storage import TransactionStore
from firebase_config import firebase_status

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    model = FraudModel(app.config["MODEL_PATH"])
    store = TransactionStore(app.config["DATABASE_PATH"])

    # Train a reproducible demonstration model on first run if no model exists.
    if not os.path.exists(app.config["MODEL_PATH"]):
        model.train_and_save(app.config["DATASET_PATH"])

    @app.context_processor
    def inject_globals():
        return {"firebase_status": firebase_status()}

    @app.get("/")
    def dashboard():
        stats = store.get_stats()
        recent = store.get_recent(8)
        return render_template("dashboard.html", stats=stats, recent=recent)

    @app.route("/predict", methods=["GET", "POST"])
    def predict():
        result = None
        if request.method == "POST":
            try:
                transaction = parse_transaction(request.form)
                result = model.predict(transaction)
                record = {**transaction, **result}
                record["source"] = "dashboard"
                store.save(record)
            except (ValueError, TypeError) as exc:
                flash(str(exc), "error")
            except Exception as exc:
                app.logger.exception("Prediction failed")
                flash(f"Prediction failed: {exc}", "error")
        return render_template("predict.html", result=result)

    @app.get("/transactions")
    def transactions():
        return render_template("transactions.html", transactions=store.get_recent(100))

    @app.get("/health")
    def health():
        return jsonify({
            "application": "SentinelGuard",
            "status": "running",
            "model_loaded": model.is_ready,
            "storage": store.backend_name,
            "firebase": firebase_status()
        })

    @app.post("/api/predict")
    def api_predict():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"error": "Send a JSON object in the request body."}), 400
        try:
            transaction = parse_transaction(payload)
            result = model.predict(transaction)
            record = {**transaction, **result, "source": "api"}
            record_id = store.save(record)
            return jsonify({"transaction_id": record_id, **result}), 200
        except (ValueError, TypeError) as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception as exc:
            app.logger.exception("API prediction failed")
            return jsonify({"error": "Prediction service error."}), 500

    @app.post("/api/retrain")
    def api_retrain():
        # Local demo endpoint. Protect this endpoint before any public deployment.
        try:
            metrics = model.train_and_save(app.config["DATASET_PATH"])
            return jsonify({"message": "Model retrained.", "metrics": metrics})
        except Exception:
            app.logger.exception("Retraining failed")
            return jsonify({"error": "Model retraining failed."}), 500

    return app

def parse_transaction(data):
    def number(name, default, minimum, maximum):
        raw = data.get(name, default)
        try:
            value = float(raw)
        except (ValueError, TypeError):
            raise ValueError(f"{name.replace('_', ' ').capitalize()} must be a number.")
        if value < minimum or value > maximum:
            raise ValueError(f"{name.replace('_', ' ').capitalize()} must be between {minimum} and {maximum}.")
        return value

    hour = int(number("hour", 12, 0, 23))
    return {
        "amount": number("amount", 1200, 1, 10000000),
        "hour": hour,
        "distance_from_home_km": number("distance_from_home_km", 5, 0, 20000),
        "is_new_device": int(number("is_new_device", 0, 0, 1)),
        "failed_attempts_24h": int(number("failed_attempts_24h", 0, 0, 50)),
        "txns_last_hour": int(number("txns_last_hour", 1, 0, 100)),
        "merchant_risk": number("merchant_risk", 0.2, 0, 1),
        "is_international": int(number("is_international", 0, 0, 1)),
    }

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=app.config["DEBUG"])
