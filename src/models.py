from schemas import TipoItem, StatusItem
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    nome_usuario = Column(String, unique=True, index=True)
    senha_hash = Column(String)
    criado_em = Column(DateTime, default=datetime.utcnow)
    itens = relationship("Item", back_populates="dono")


class Item(Base):
    __tablename__ = "itens"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, index=True)
    tipo = Column(SQLEnum(TipoItem))
    status = Column(SQLEnum(StatusItem))
    descricao = Column(String, nullable=True)
    avaliacao = Column(Integer, nullable=True)
    tags = Column(String)
    favorito = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
    id_dono = Column(Integer, ForeignKey("usuarios.id"))
    dono = relationship("Usuario", back_populates="itens")
