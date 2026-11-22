import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from config import Config
from firebase_config import get_firestore

class TransactionStore:
    def __init__(self, db_path):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.firestore = None
        if Config.STORAGE_BACKEND in ("auto", "firestore"):
            self.firestore = get_firestore()
        if Config.STORAGE_BACKEND == "firestore" and self.firestore is None:
            raise RuntimeError("STORAGE_BACKEND=firestore but Firebase is not connected.")
        self.backend_name = "Firestore" if self.firestore is not None else "SQLite (local fallback)"
        self._init_sqlite()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_sqlite(self):
        with self._connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY, created_at TEXT NOT NULL, data TEXT NOT NULL
            )""")

    def save(self, record):
        record_id = str(uuid.uuid4())
        item = dict(record)
        item["created_at"] = datetime.now(timezone.utc).isoformat()
        if self.firestore is not None:
            self.firestore.collection(Config.FIRESTORE_COLLECTION).document(record_id).set(item)
        with self._connect() as conn:
            conn.execute("INSERT INTO transactions (id, created_at, data) VALUES (?, ?, ?)",
                         (record_id, item["created_at"], json.dumps(item)))
        return record_id

    def get_recent(self, limit=100):
        with self._connect() as conn:
            rows = conn.execute("SELECT data FROM transactions ORDER BY created_at DESC LIMIT ?",
                                (limit,)).fetchall()
        return [json.loads(row["data"]) for row in rows]

    def get_stats(self):
        rows = self.get_recent(100000)
        total = len(rows)
        fraud = sum(1 for x in rows if x.get("prediction") == "Fraud")
        return {
            "total": total,
            "fraud": fraud,
            "genuine": total - fraud,
            "fraud_rate": round((fraud / total) * 100, 1) if total else 0
        }
