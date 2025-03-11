import os
import datetime
from datetime import timedelta
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer

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
    expires = datetime.utcnow() + timedelta(
        minutes=int(os.getenv("JWT_EXPIRATION_MINUTES", 30)))
    data["exp"] = expires
    return jwt.encode(data, os.getenv("JWT_SECRET"), algorithm=os.getenv("JWT_ALGORITHM"))