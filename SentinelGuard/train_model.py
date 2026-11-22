from config import Config
from model_service import FraudModel

if __name__ == "__main__":
    service = FraudModel(Config.MODEL_PATH)
    metrics = service.train_and_save(Config.DATASET_PATH)
    print("Model training completed.")
    for name, value in metrics.items():
        print(f"{name}: {value}")
    print(f"Saved model: {Config.MODEL_PATH}")
