import jwt
from datetime import datetime, timedelta, timezone
import bcrypt
from fastapi import HTTPException, Request
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from models import Usuario

SECRET_KEY = "biblioteca_api_secret_key"
ALGORITHM = "HS256"
MINUTOS_EXPIRACAO_TOKEN = 30

api_key_header = APIKeyHeader(name="Authorization")

def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado, faça login novamente")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

async def get_token(request: Request):
    # Try to get token from Authorization header
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ")[1]
    
    # Try to get token from cookies
    token = request.cookies.get("access_token")
    if token:
        if token.startswith("Bearer "):
            return token[7:]
        return token
    
    raise HTTPException(status_code=401, detail="Token JWT não fornecido corretamente")

async def get_current_user(request: Request):
    token = await get_token(request)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado, faça login novamente")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user or not verify_password(password, user.senha_hash):
        return None
    return user
