from pymongo import MongoClient
from config import MONGO_URI, DB_NAME
import certifi

client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    retryWrites=True,
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
    socketTimeoutMS=10000
)

# test connection 
client.admin.command("ping")

db = client[DB_NAME]

documents_collection = db["documents"]
chat_sessions_collection = db["chat_sessions"]