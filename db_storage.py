# db_storage.py
# Manglish comments & strings inside
import os
from pymongo import MongoClient, ReturnDocument
from typing import List, Dict, Any
from datetime import datetime

MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB", "eldro_bot")
COLLECTION = os.getenv("MONGODB_COLLECTION", "users")

if not MONGO_URI:
    raise RuntimeError("Set MONGODB_URI env var (MongoDB Atlas connection string)")

# Create client (connection pooling handled by pymongo)
_client = MongoClient(MONGO_URI)
_db = _client[DB_NAME]
_users = _db[COLLECTION]

# Ensure index on id for fast lookup and uniqueness
try:
    _users.create_index("id", unique=True)
except Exception:
    pass

def add_or_update_user(user_id: int, username: str = None, first_name: str = None):
    """
    Manglish: User register cheyyuka or update last_seen.
    Stores:
      { id: int, username: str, first_name: str, last_seen: ISOstr }
    """
    now = datetime.utcnow().isoformat()
    doc = {"id": user_id, "last_seen": now}
    if username:
        doc["username"] = username
    if first_name:
        doc["first_name"] = first_name
    # Upsert (insert or update)
    _users.find_one_and_update(
        {"id": user_id},
        {"$set": doc},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )

def get_all_user_ids() -> List[int]:
    """Manglish: return list of user ids"""
    rows = _users.find({}, {"id": 1})
    return [int(r["id"]) for r in rows]

def get_all_users() -> Dict[str, Any]:
    """
    Manglish: Return dict keyed by id (string) to user doc.
    Note: document objects contain _id (ObjectId) — we omit it.
    """
    out = {}
    for r in _users.find({}):
        uid = str(r.get("id"))
        # remove Mongo internal fields if present
        r.pop("_id", None)
        out[uid] = r
    return out

def user_count() -> int:
    return _users.count_documents({})

def clear_db():
    """Manglish: only for dev/testing. Drops collection contents."""
    _users.delete_many({})

# Optional helpers
def remove_user(user_id: int):
    _users.delete_one({"id": user_id})

def get_user(user_id: int) -> Dict[str, Any]:
    r = _users.find_one({"id": user_id}, {"_id": 0})
    return r or {}
