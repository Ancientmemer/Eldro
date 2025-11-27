# migrate_json_to_mongo.py
# Manglish comments ok inside code if you want; this is plain Python
import json
import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB", "eldro_bot")
COL = os.getenv("MONGODB_COLLECTION", "users")
DB_FILE = "storage.json"

if not MONGO_URI:
    raise RuntimeError("Set MONGODB_URI env var before running this script")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users_col = db[COL]

with open(DB_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

for k, v in data.items():
    try:
        uid = int(k)
    except:
        uid = int(v.get("id", k))
    v["id"] = uid
    users_col.update_one({"id": uid}, {"$set": v}, upsert=True)

print("Migration finished: imported", len(data), "users.")
