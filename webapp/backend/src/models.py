from pydantic import BaseModel
from typing import Optional

class MigrationTask(BaseModel):
    task_id: str
    status: str
    progress: Optional[dict] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserInDB(BaseModel):
    username: str
    hashed_password: str