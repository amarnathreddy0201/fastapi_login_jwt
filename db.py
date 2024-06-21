from typing import List, Dict, Any
import logging
import motor.motor_asyncio
from beanie import Document
from fastapi_users.db import  BeanieBaseUser, BeanieUserDatabase,BaseOAuthAccount
from pydantic import Field

# Logger configuration
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "mongodb://localhost:27023"
client = motor.motor_asyncio.AsyncIOMotorClient(
    DATABASE_URL, uuidRepresentation="standard"
)
db = client["database"]

class OAuthAccount(BaseOAuthAccount):
    pass

class User(BeanieBaseUser, Document):
    doubts: List[Dict[str, Any]] = Field(default_factory=list)
    oauth_accounts: List[OAuthAccount] = Field(default_factory=list)
    role: str = Field(default="user")
    count_requests: List[Dict[str, Any]] = Field(default_factory=list)

async def get_user_db():
    logger.info("Retrieving user database")
    yield BeanieUserDatabase(User, OAuthAccount)

logger.info("Database connection initialized")

# You might want to handle potential exceptions that can occur during database connection
# For example, catching exceptions during the client connection setup
try:
    client = motor.motor_asyncio.AsyncIOMotorClient(
        DATABASE_URL, uuidRepresentation="standard"
    )
    db = client["alvisionpi"]
    logger.info("Connected to MongoDB")
except Exception as e:
    logger.error(f"Error connecting to MongoDB: {e}")
