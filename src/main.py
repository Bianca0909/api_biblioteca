from datetime import timedelta
from fastapi import FastAPI, Request, HTTPException, Depends, status, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import get_db, engine
from models import Base, Item, Usuario
from schemas import ItemCreate, ItemUpdate
from auth import create_token, hash_password, verify_password, get_current_user, MINUTOS_EXPIRACAO_TOKEN

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Biblioteca Pessoal",
    description="API para gerenciar uma biblioteca pessoal de livros, filmes e séries",
    version="1.0.0",
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def pagina_inicial(request: Request, db: Session = Depends(get_db)):
    try:
        email = await get_current_user(request)
        usuario = db.query(Usuario).filter(Usuario.email == email).first()
    except HTTPException:
        usuario = None
    return templates.TemplateResponse("home.html", {"request": request, "usuario_atual": usuario})


@app.get("/login", response_class=HTMLResponse)
async def pagina_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/registrar", response_class=HTMLResponse)
async def pagina_registro(request: Request):
    return templates.TemplateResponse("registrar.html", {"request": request, "erro": None})


@app.get("/itens", response_class=HTMLResponse)
async def pagina_itens(
    request: Request,
    db: Session = Depends(get_db),
    usuario_atual: str = Depends(get_current_user),
):
    usuario = db.query(Usuario).filter(Usuario.email == usuario_atual).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    itens = db.query(Item).filter(Item.id_dono == usuario.id).all()
    for item in itens:
        item.tags = [tag.strip() for tag in item.tags.split(",")] if item.tags else []
    return templates.TemplateResponse(
        "listar_itens.html", {"request": request, "itens": itens, "usuario_atual": usuario_atual}
    )

@app.get("/itens/criar", response_class=HTMLResponse)
async def pagina_criar_item(request: Request, db: Session = Depends(get_db)):
    try:
        email = await get_current_user(request)
        usuario = db.query(Usuario).filter(Usuario.email == email).first()
        return templates.TemplateResponse("criar_item.html", {"request": request, "usuario_atual": usuario, "item": None})
    except HTTPException:
        return RedirectResponse(url="/login", status_code=303)

@app.post("/itens/criar", status_code=status.HTTP_201_CREATED)
async def criar_item(
    request: Request,
    item: ItemCreate,
    db: Session = Depends(get_db),
    usuario_atual: str = Depends(get_current_user),
):
    request_data = await request.json()
    try:
        item = ItemCreate(**request_data)
    except Exception as e:
        raise
    usuario = db.query(Usuario).filter(Usuario.email == usuario_atual).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    db_item = Item(
        titulo=item.titulo,
        tipo=item.tipo,
        status=item.status,
        descricao=item.descricao,
        avaliacao=item.avaliacao,
        tags=",".join(item.tags),
        favorito=item.favorito,
        id_dono=usuario.id,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/itens/{item_id}", response_class=HTMLResponse)
async def pagina_detalhe_item(
    request: Request,
    item_id: int,
    db: Session = Depends(get_db),
    usuario_atual: str = Depends(get_current_user),
):
    item = (
        db.query(Item)
        .join(Usuario)
        .filter(Item.id == item_id, Usuario.email == usuario_atual)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    # Convert comma-separated tags to list
    item.tags = [tag.strip() for tag in item.tags.split(",")] if item.tags else []
    
    return templates.TemplateResponse(
        "detalhe_item.html", {"request": request, "item": item, "usuario_atual": usuario_atual}
    )


import re

def validar_email(email: str) -> bool:
    padrao = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return bool(padrao.match(email))

def validar_senha(senha: str) -> tuple[bool, str]:
    if len(senha) < 8:
        return False, "A senha deve ter pelo menos 8 caracteres"
    if not re.search(r'[A-Z]', senha):
        return False, "A senha deve conter pelo menos uma letra maiúscula"
    if not re.search(r'[a-z]', senha):
        return False, "A senha deve conter pelo menos uma letra minúscula"
    if not re.search(r'\d', senha):
        return False, "A senha deve conter pelo menos um número"
    return True, ""

@app.post("/registrar", response_class=HTMLResponse)
async def registrar_usuario(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    email = form.get("email")
    nome_usuario = form.get("nome_usuario")
    senha = form.get("senha")

    if not all([email, nome_usuario, senha]):
        return templates.TemplateResponse(
            "registrar.html",
            {"request": request, "erro": "Todos os campos são obrigatórios"},
            status_code=400
        )
        
    if not validar_email(email):
        return templates.TemplateResponse(
            "registrar.html",
            {"request": request, "erro": "Email inválido"},
            status_code=400
        )
        
    senha_valida, erro_senha = validar_senha(senha)
    if not senha_valida:
        return templates.TemplateResponse(
            "registrar.html",
            {"request": request, "erro": erro_senha},
            status_code=400
        )

    db_usuario = (
        db.query(Usuario)
        .filter(
            (Usuario.email == email)
            | (Usuario.nome_usuario == nome_usuario)
        )
        .first()
    )
    if db_usuario:
        return templates.TemplateResponse(
            "registrar.html",
            {"request": request, "erro": "Email ou nome de usuário já registrado"},
            status_code=400
        )

    senha_hash = hash_password(senha)
    db_usuario = Usuario(
        email=email, nome_usuario=nome_usuario, senha_hash=senha_hash
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)

    # After successful registration, redirect to login page
    return RedirectResponse(url="/login", status_code=303)


@app.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    email = form.get("email")
    senha = form.get("senha")

    db_usuario = db.query(Usuario).filter(Usuario.email == email).first()

    if not db_usuario or not verify_password(senha, db_usuario.senha_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Email ou senha inválidos"},
            status_code=400,
        )

    token = create_token({"sub": db_usuario.email}, timedelta(minutes=MINUTOS_EXPIRACAO_TOKEN))
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
    return response


@app.get("/itens")
async def listar_itens(
    request: Request,
    db: Session = Depends(get_db),
    usuario_atual: str = Depends(get_current_user),
):
    usuario = db.query(Usuario).filter(Usuario.email == usuario_atual).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    
    itens = db.query(Item).filter(Item.id_dono == usuario.id).all()
    # Convert comma-separated tags to lists
    for item in itens:
        item.tags = [tag.strip() for tag in item.tags.split(",")] if item.tags else []
    
    return templates.TemplateResponse(
        "listar_itens.html", 
        {"request": request, "itens": itens, "usuario_atual": usuario_atual}
    )


@app.get("/itens/{item_id}")
async def obter_item(
    request: Request,
    item_id: int,
    db: Session = Depends(get_db),
    usuario_atual: str = Depends(get_current_user),
):
    item = (
        db.query(Item)
        .join(Usuario)
        .filter(Item.id == item_id, Usuario.email == usuario_atual)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return item


@app.get("/itens/{item_id}/editar", response_class=HTMLResponse)
async def pagina_editar_item(
    request: Request,
    item_id: int,
    db: Session = Depends(get_db),
    usuario_atual: str = Depends(get_current_user),
):
    item = (
        db.query(Item)
        .join(Usuario)
        .filter(Item.id == item_id, Usuario.email == usuario_atual)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    item.tags = [tag.strip() for tag in item.tags.split(",")] if item.tags else []
    
    return templates.TemplateResponse(
        "criar_item.html",
        {"request": request, "item": item, "usuario_atual": usuario_atual}
    )

@app.post("/itens/{item_id}/editar")
async def atualizar_item(
    request: Request,
    item_id: int,
    db: Session = Depends(get_db),
    usuario_atual: str = Depends(get_current_user),
):
    db_item = (
        db.query(Item)
        .join(Usuario)
        .filter(Item.id == item_id, Usuario.email == usuario_atual)
        .first()
    )
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    data = await request.json()
    
    try:
        update_data = ItemUpdate(**data)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    for field, value in update_data.dict(exclude_unset=True).items():
        if field == "tags":
            value = ",".join(value)
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)
    return db_item


@app.post("/itens/{item_id}/deletar", status_code=status.HTTP_303_SEE_OTHER)
async def deletar_item(
    request: Request,
    item_id: int,
    db: Session = Depends(get_db),
    usuario_atual: str = Depends(get_current_user),
):
    item = (
        db.query(Item)
        .join(Usuario)
        .filter(Item.id == item_id, Usuario.email == usuario_atual)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    db.delete(item)
    db.commit()
    return RedirectResponse(url="/itens", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/logout")
async def logout(response: Response):
    response.delete_cookie(key="token")
    return RedirectResponse(url="/login", status_code=303)
