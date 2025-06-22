from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db, engine
from models import Base, Item, Usuario
from schemas import (
    ItemCreate,
    UsuarioCreate,
    LoginUsuario,
    TipoItem,
    StatusItem,
    ItemUpdate,
)
from auth import hash_senha, verificar_senha, obter_usuario_atual

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Biblioteca Pessoal",
    description="API para gerenciar uma biblioteca pessoal de livros, filmes e séries",
    version="1.0.0",
)

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def pagina_inicial(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def pagina_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/registrar", response_class=HTMLResponse)
async def pagina_registro(request: Request):
    return templates.TemplateResponse("registrar.html", {"request": request})


@app.get("/itens", response_class=HTMLResponse)
async def pagina_itens(
    request: Request,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    itens = db.query(Item).filter(Item.id_dono == usuario_atual.id).all()
    return templates.TemplateResponse(
        "listar_itens.html", {"request": request, "itens": itens}
    )


@app.get("/itens/{item_id}", response_class=HTMLResponse)
async def pagina_detalhe_item(
    request: Request,
    item_id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    item = (
        db.query(Item)
        .filter(Item.id == item_id, Item.id_dono == usuario_atual.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return templates.TemplateResponse(
        "detalhe_item.html", {"request": request, "item": item}
    )


@app.post("/registrar")
def registrar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    db_usuario = (
        db.query(Usuario)
        .filter(
            (Usuario.email == usuario.email)
            | (Usuario.nome_usuario == usuario.nome_usuario)
        )
        .first()
    )
    if db_usuario:
        raise HTTPException(
            status_code=400, detail="Email ou nome de usuário já registrado"
        )

    senha_hash = hash_senha(usuario.senha)
    db_usuario = Usuario(
        email=usuario.email, nome_usuario=usuario.nome_usuario, senha_hash=senha_hash
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario


@app.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    email = form.get("email")
    senha = form.get("senha")

    db_usuario = db.query(Usuario).filter(Usuario.email == email).first()

    if not db_usuario or not verificar_senha(senha, db_usuario.senha_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Email ou senha inválidos"},
            status_code=400,
        )

    # Redireciona para a página inicial após login bem-sucedido
    return RedirectResponse(url="/", status_code=303)


@app.post("/itens/criar")  # 3
def criar_item(
    item: ItemCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    db_item = Item(
        titulo=item.titulo,
        tipo=item.tipo,
        status=item.status,
        descricao=item.descricao,
        avaliacao=item.avaliacao,
        tags=",".join(item.tags),
        favorito=item.favorito,
        id_dono=usuario_atual.id,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.get("/itens")  # 4
def listar_itens(
    tipo: Optional[TipoItem] = None,
    status: Optional[StatusItem] = None,
    tag: Optional[str] = None,
    favorito: Optional[bool] = None,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    query = db.query(Item).filter(Item.id_dono == usuario_atual.id)

    if tipo:
        query = query.filter(Item.tipo == tipo)
    if status:
        query = query.filter(Item.status == status)
    if tag:
        query = query.filter(Item.tags.like(f"%{tag}%"))
    if favorito is not None:
        query = query.filter(Item.favorito == favorito)

    return query.all()


@app.get("/itens/{item_id}")
def obter_item(
    item_id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    item = (
        db.query(Item)
        .filter(Item.id == item_id, Item.id_dono == usuario_atual.id)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return item


@app.put("/itens/{item_id}")
def atualizar_item(
    item_id: int,
    item: ItemUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    db_item = (
        db.query(Item)
        .filter(Item.id == item_id, Item.id_dono == usuario_atual.id)
        .first()
    )
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    update_data = item.dict(exclude_unset=True)

    if "tags" in update_data:
        update_data["tags"] = ",".join(update_data["tags"])

    for field, value in update_data.items():
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)
    return db_item


@app.post("/itens/{item_id}/deletar", status_code=status.HTTP_303_SEE_OTHER)
def deletar_item(
    item_id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    item = (
        db.query(Item)
        .filter(Item.id == item_id, Item.id_dono == usuario_atual.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    db.delete(item)
    db.commit()
    return RedirectResponse(url="/itens", status_code=status.HTTP_303_SEE_OTHER)
