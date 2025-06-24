import jwt
from datetime import datetime, timedelta, timezone
import bcrypt
from fastapi import HTTPException, Security, Depends, Request
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from models import Usuario
import schemas
from database import get_db

CHAVE_SECRETA = "biblioteca_api_secret_key"
ALGORITMO = "HS256"
MINUTOS_EXPIRACAO_TOKEN = 30

api_key_header = APIKeyHeader(name="Authorization")

def get_token_from_cookie(request: Request) -> str:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Não autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Remove 'Bearer ' prefix if present
    if token.startswith("Bearer "):
        token = token[7:]
    return token


def criar_token_acesso(data: dict):
    dados = data.copy()
    expiracao = datetime.now(timezone.utc) + timedelta(minutes=MINUTOS_EXPIRACAO_TOKEN)
    dados.update({"exp": expiracao})
    token = jwt.encode(dados, CHAVE_SECRETA, algorithm=ALGORITMO)
    return token


def verificar_token(token: str):
    try:
        payload = jwt.decode(token, CHAVE_SECRETA, algorithms=[ALGORITMO])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401, detail="Token expirado, faça login novamente"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


def obter_usuario_atual(
    request: Request,
    db: Session = Depends(get_db)
) -> Usuario:
    token = get_token_from_cookie(request)
    erro_credenciais = HTTPException(
        status_code=401,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, CHAVE_SECRETA, algorithms=[ALGORITMO])
        email: str = payload.get("sub")
        if email is None:
            raise erro_credenciais
        dados_token = schemas.TokenData(email=email)
    except jwt.JWTError:
        raise erro_credenciais

    usuario = db.query(Usuario).filter(Usuario.email == dados_token.email).first()
    if usuario is None:
        raise erro_credenciais
    return usuario


def hash_senha(senha: str) -> str:
    salt = bcrypt.gensalt()
    hash_senha = bcrypt.hashpw(senha.encode(), salt)
    return hash_senha.decode()


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode(), senha_hash.encode())


def autenticar_usuario(db: Session, email: str, senha: str):
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario or not verificar_senha(senha, usuario.senha_hash):
        return None
    return usuario
