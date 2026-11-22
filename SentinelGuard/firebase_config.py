import os
import firebase_admin
from firebase_admin import credentials, firestore
from config import Config

_db = None
_error = None

def get_firestore():
    global _db, _error
    if _db is not None:
        return _db
    path = Config.FIREBASE_CREDENTIALS
    if not os.path.isfile(path):
        _error = "Firebase credentials not found; using local SQLite storage."
        return None
    try:
        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate(path))
        _db = firestore.client()
        _error = None
        return _db
    except Exception as exc:
        _error = str(exc)
        return None

def firebase_status():
    db = get_firestore()
    return {"connected": db is not None, "message": "Connected" if db else (_error or "Not configured")}
