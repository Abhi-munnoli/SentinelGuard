from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "sentinelguard.db"
DB_PATH.parent.mkdir(exist_ok=True)
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    amount = Column(Float, nullable=False)
    hour = Column(Integer, nullable=False)
    distance_from_home = Column(Float, nullable=False)
    merchant_risk = Column(Float, nullable=False)
    transaction_velocity = Column(Integer, nullable=False)
    is_foreign = Column(Integer, nullable=False)
    device_changed = Column(Integer, nullable=False)
    fraud_probability = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(12), nullable=False)
    prediction = Column(Integer, nullable=False)
    explanation = Column(JSON, nullable=True)

Base.metadata.create_all(bind=engine)
