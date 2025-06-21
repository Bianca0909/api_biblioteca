import jwt
from datetime import datetime, timedelta, timezone
import bcrypt
from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy.orm import Session
import models
import schemas
from database import obter_sessao_bd

CHAVE_SECRETA = "biblioteca_api_secret_key"  # Em produção, usar variável de ambiente
ALGORITMO = "HS256"
MINUTOS_EXPIRACAO_TOKEN = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
api_key_header = APIKeyHeader(name="Authorization")

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
        raise HTTPException(status_code=401, detail="Token expirado, faça login novamente")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

def obter_usuario_atual(
    db: Session = Depends(obter_sessao_bd),
    token: str = Depends(oauth2_scheme)
) -> models.Usuario:
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
    
    usuario = db.query(models.Usuario).filter(models.Usuario.email == dados_token.email).first()
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
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not usuario or not verificar_senha(senha, usuario.senha_hash):
        return None
    return usuario
