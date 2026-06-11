"""
seed.py  —  run once to load data/db.json into MongoDB

  pip install pymongo
  python seed.py

After seeding, start the app normally:  python app.py
"""
import json
import os
from pathlib import Path
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure

#We are gonna keep all of our uri and databse name keys within our environment variables for safety purposes
MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME   = os.environ.get("DB_NAME")

#Check to see if our code successfully extracted the values for the variable names stored within our environment
print(MONGO_URI)
print(DB_NAME)


MONGO_URI = "mongodb://localhost:27017/"
DB_NAME   = "kirchoff_db"

def seed():
    # ── connect ──────────────────────────────────────
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000) #Has three seconds to connect to the mongodb server
        client.admin.command("ping")          # raises if MongoDB isn't running
    except ConnectionFailure:
        print("✗  Could not connect to MongoDB at", MONGO_URI)
        print("   Make sure mongod is running:  mongod --dbpath /data/db")
        return

    db = client[DB_NAME]

    # ── load JSON ─────────────────────────────────────
    try:
        data_file = Path(__file__).parent / "data" / "db.json"
        with open(data_file, "r", encoding="utf-8") as f:
            src = json.load(f)
    except FileNotFoundError:
        print("Couldn't find data file")


    # ── seed each collection ──────────────────────────
    for col_name in ("properties", "notes", "saved_properties"):
        col   = db[col_name]
        docs  = src.get(col_name, []) #Retrieves all the JSON data under that column name
        col.drop()


        if docs:
            col.insert_many(docs)
            print(f"  ✓  {col_name}: inserted {len(docs)} documents")
        else:
            print(f"  –  {col_name}: empty (collection created, no documents)")

    # ── indexes ───────────────────────────────────────
    db.properties.create_index("property_id", unique=True)
    db.properties.create_index("qct_status")
    db.properties.create_index("terrain_level")
    db.properties.create_index("price")
    db.properties.create_index("size_acres")

    db.notes.create_index("property_id")
    db.notes.create_index("user_id")

    db.saved_properties.create_index(
        [("user_id", ASCENDING), ("property_id", ASCENDING)], unique=True
    )
    print("  ✓  indexes created")

    client.close()
    print("\n✓  Seeding complete — run  python app.py  to start the server.")

if __name__ == "__main__":
    seed()