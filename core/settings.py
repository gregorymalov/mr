from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB
class DatabaseSettings:
    client = AsyncIOMotorClient("mongodb+srv://meizu:PasFusQwe167@cluster666.sqva8jf.mongodb.net/?retryWrites=true&w=majority")
    db = client["MRx0"]
    machines = db["machines"]
    blocks = db["blocks"]

db_settings = DatabaseSettings()