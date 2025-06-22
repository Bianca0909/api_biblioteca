from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from enum import Enum


class TipoItem(str, Enum):
    LIVRO = "livro"
    FILME = "filme"
    SERIE = "serie"


class StatusItem(str, Enum):
    PARA_LER = "para_ler"
    LENDO = "lendo"
    COMPLETADO = "completado"


class ItemCreate(BaseModel):
    titulo: str
    tipo: TipoItem
    status: StatusItem
    descricao: Optional[str] = None
    avaliacao: Optional[int] = None
    tags: List[str] = []
    favorito: bool = False


class ItemUpdate(BaseModel):
    titulo: Optional[str] = None
    tipo: Optional[TipoItem] = None
    status: Optional[StatusItem] = None
    descricao: Optional[str] = None
    avaliacao: Optional[int] = None
    tags: Optional[List[str]] = None
    favorito: Optional[bool] = None


class Item(BaseModel):
    id: int
    titulo: str
    tipo: TipoItem
    status: StatusItem
    descricao: Optional[str] = None
    avaliacao: Optional[int] = None
    tags: List[str] = []
    favorito: bool = False
    criado_em: datetime
    id_dono: int

    class Config:
        from_attributes = True


class UsuarioCreate(BaseModel):
    email: EmailStr
    nome_usuario: str
    senha: str


class Usuario(BaseModel):
    id: int
    email: EmailStr
    nome_usuario: str


class LoginUsuario(BaseModel):
    email: EmailStr
    senha: str


class Token(BaseModel):
    access_token: str
    token_type: str
