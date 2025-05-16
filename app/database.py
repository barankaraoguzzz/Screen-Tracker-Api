from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId
import os

# MongoDB bağlantı ayarları
MONGO_DETAILS = os.getenv("MONGO_DETAILS", "mongodb://localhost:27017")

client = AsyncIOMotorClient(MONGO_DETAILS)

# Veritabanı ve koleksiyonlar
database = client.screen_tracker
tenants_collection = database.get_collection("tenants")
users_collection = database.get_collection("users")
projects_collection = database.get_collection("projects")
sessions_collection = database.get_collection("sessions")
screens_collection = database.get_collection("screens")
events_collection = database.get_collection("events")
invitation_tokens_collection = database.get_collection("invitation_tokens")

# BSON ObjectId'yi string'e çeviren yardımcı fonksiyon
def object_id_to_str(obj_id):
    return str(obj_id) 