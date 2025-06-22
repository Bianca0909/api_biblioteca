from database import engine
from models import Base


def create_database():
    Base.metadata.create_all(bind=engine)
    print("Banco de dados criado com sucesso!")


if __name__ == "__main__":
    create_database()
