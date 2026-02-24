import bcrypt
from pymongo import MongoClient
from datetime import datetime
import os

class MongoDB:
    def __init__(self):
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client.oracle_forensic_v2
        self.users = self.db.users
        self.cases = self.db.cases

    # ---------- USERS ----------
    def create_user(self, username, password):
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        self.users.insert_one({
            "username": username,
            "password": hashed
        })

    def get_user(self, username, password):
        user = self.users.find_one({"username": username})
        if not user:
            return None

        stored = user["password"]
        if bcrypt.checkpw(password.encode(), stored):
            return user
        return None

    # ---------- CASES ----------
    def save_case(self, data):
        data["created_at"] = datetime.utcnow()
        self.cases.insert_one(data)

    def get_cases_by_user(self, user):
        return list(self.cases.find({"user": user}).sort("created_at", -1))

    def get_case(self, case_id, user):
        return self.cases.find_one({"case_id": case_id, "user": user})

    def delete_case(self, case_id, user):
        self.cases.delete_one({"case_id": case_id, "user": user})