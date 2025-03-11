import os
import logger
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from ..models import Token, UserInDB
from datetime import timedelta, datetime
from jose import jwt, JWTError
from passlib.context import CryptContext

router = APIRouter(tags=["Authentication"])

fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": "$2b$12$EixZaYVK1fsbY1eIYvB.OLU2gZ/2ZgWR7Q3KZ1GZ1V1yLdZkH4tW",
    }
}

# Set up password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or not pwd_context.verify(form_data.password, user["hashed_password"]):
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    access_token_expires = timedelta(minutes=int(os.getenv("JWT_EXPIRATION_MINUTES", 30)))
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

async def validate_ip(request: Request, token: str = Depends(OAuth2PasswordBearer(tokenUrl="token"))) -> str:
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=[os.getenv("JWT_ALGORITHM")])
        client_ip = request.client.host
        if payload["ip"] != client_ip:
            raise HTTPException(status_code=403, detail="Invalid token origin")
        return payload
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid credentials")

def create_access_token(data: dict, client_ip: str):
    data["ip"] = client_ip
    expires = datetime.timezone.utc() + timedelta(
        minutes=int(os.getenv("JWT_EXPIRATION_MINUTES", 30)))
    data["exp"] = expires
    return jwt.encode(data, os.getenv("JWT_SECRET"), algorithm=os.getenv("JWT_ALGORITHM"))
