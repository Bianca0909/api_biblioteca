from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

URL_BANCO_DADOS = "sqlite:///./biblioteca.db"

engine = create_engine(URL_BANCO_DADOS, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autoflush=False, bind=engine)
Base = declarative_base()


# Dependência para obter sessão do BD
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
