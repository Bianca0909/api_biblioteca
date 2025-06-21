from pydantic import BaseModel, EmailStr
from typing import List, Optional, ForwardRef, Annotated
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

class ItemBase(BaseModel):
    titulo: str
    tipo: TipoItem
    status: StatusItem
    descricao: Optional[str] = None
    avaliacao: Optional[int] = None
    tags: List[str] = []
    favorito: bool = False

class ItemCreate(ItemBase):
    pass

class ItemUpdate(ItemBase):
    titulo: Optional[str] = None
    tipo: Optional[TipoItem] = None
    status: Optional[StatusItem] = None

class Item(ItemBase):
    id: int
    criado_em: datetime
    id_dono: int

    class Config:
        from_attributes = True

class UsuarioBase(BaseModel):
    email: EmailStr
    nome_usuario: str

class CriarUsuario(UsuarioBase):
    senha: str

class Usuario(UsuarioBase):
    id: int
    criado_em: datetime
    itens: List['Item'] = []

    class Config:
        from_attributes = True

class LoginUsuario(BaseModel):
    email: EmailStr
    senha: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Update forward references
Usuario.update_forward_refs()
