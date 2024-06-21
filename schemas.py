from beanie import PydanticObjectId
from fastapi_users import schemas
from typing import Optional
from db import User

class UserRead(schemas.BaseUser[PydanticObjectId]):
    pass

class UserCreate(schemas.BaseUserCreate):
    role: Optional[str] = None

class UserUpdate(schemas.BaseUserUpdate):
    pass

class UserDB(User):
    pass