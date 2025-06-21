
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import models
import schemas
from database import engine, obter_sessao_bd
from auth import hash_senha, autenticar_usuario, criar_token_acesso, obter_usuario_atual

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Biblioteca Pessoal",
    description="API para gerenciar uma biblioteca pessoal de livros, filmes e séries",
    version="1.0.0"
)

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def pagina_inicial(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def pagina_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/registrar", response_class=HTMLResponse)
async def pagina_registro(request: Request):
    return templates.TemplateResponse("registrar.html", {"request": request})

@app.get("/itens", response_class=HTMLResponse)
async def pagina_itens(request: Request, db: Session = Depends(obter_sessao_bd), usuario_atual: models.Usuario = Depends(obter_usuario_atual)):
    itens = db.query(models.Item).filter(models.Item.id_dono == usuario_atual.id).all()
    return templates.TemplateResponse("listar_itens.html", {
        "request": request,
        "itens": itens
    })

@app.get("/itens/{item_id}", response_class=HTMLResponse)
async def pagina_detalhe_item(request: Request, item_id: int, db: Session = Depends(obter_sessao_bd), usuario_atual: models.Usuario = Depends(obter_usuario_atual)):
    item = db.query(models.Item).filter(
        models.Item.id == item_id,
        models.Item.id_dono == usuario_atual.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return templates.TemplateResponse("detalhe_item.html", {
        "request": request,
        "item": item
    })

@app.post("/registrar", response_model=schemas.Usuario)
def registrar_usuario(usuario: schemas.CriarUsuario, db: Session = Depends(obter_sessao_bd)):
    db_usuario = db.query(models.Usuario).filter(
        (models.Usuario.email == usuario.email) |
        (models.Usuario.nome_usuario == usuario.nome_usuario)
    ).first()
    if db_usuario:
        raise HTTPException(
            status_code=400,
            detail="Email ou nome de usuário já registrado"
        )
    
    senha_hash = hash_senha(usuario.senha)
    db_usuario = models.Usuario(
        email=usuario.email,
        nome_usuario=usuario.nome_usuario,
        senha_hash=senha_hash
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(obter_sessao_bd)):
    usuario = autenticar_usuario(db, form_data.username, form_data.password)
    if not usuario:
        raise HTTPException(
            status_code=401,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_acesso = criar_token_acesso(data={"sub": usuario.email})
    return {"access_token": token_acesso, "token_type": "bearer"}

@app.post("/itens", response_model=schemas.Item, status_code=status.HTTP_201_CREATED)
def criar_item(
    item: schemas.ItemCreate,
    db: Session = Depends(obter_sessao_bd),
    usuario_atual: models.Usuario = Depends(obter_usuario_atual)
):
    db_item = models.Item(
        titulo=item.titulo,
        tipo=item.tipo,
        status=item.status,
        descricao=item.descricao,
        avaliacao=item.avaliacao,
        tags=','.join(item.tags),
        favorito=item.favorito,
        id_dono=usuario_atual.id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/itens", response_model=List[schemas.Item])
def listar_itens(
    tipo: Optional[schemas.TipoItem] = None,
    status: Optional[schemas.StatusItem] = None,
    tag: Optional[str] = None,
    favorito: Optional[bool] = None,
    db: Session = Depends(obter_sessao_bd),
    usuario_atual: models.Usuario = Depends(obter_usuario_atual)
):
    query = db.query(models.Item).filter(models.Item.id_dono == usuario_atual.id)
    
    if tipo:
        query = query.filter(models.Item.tipo == tipo)
    if status:
        query = query.filter(models.Item.status == status)
    if tag:
        query = query.filter(models.Item.tags.contains(tag))
    if favorito is not None:
        query = query.filter(models.Item.favorito == favorito)
    
    return query.all()

@app.get("/itens/{item_id}", response_model=schemas.Item)
def obter_item(
    item_id: int,
    db: Session = Depends(obter_sessao_bd),
    usuario_atual: models.Usuario = Depends(obter_usuario_atual)
):
    item = db.query(models.Item).filter(
        models.Item.id == item_id,
        models.Item.id_dono == usuario_atual.id
    ).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return item

@app.put("/itens/{item_id}", response_model=schemas.Item)
def atualizar_item(
    item_id: int,
    item: schemas.ItemUpdate,
    db: Session = Depends(obter_sessao_bd),
    usuario_atual: models.Usuario = Depends(obter_usuario_atual)
):
    db_item = db.query(models.Item).filter(
        models.Item.id == item_id,
        models.Item.owner_id == current_user.id
    ).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    update_data = item.dict(exclude_unset=True)
    
    if 'tags' in update_data:
        update_data['tags'] = ','.join(update_data['tags'])
    
    for field, value in update_data.items():
        setattr(db_item, field, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item

@app.post("/itens/{item_id}/deletar", status_code=status.HTTP_303_SEE_OTHER)
def deletar_item(
    item_id: int,
    db: Session = Depends(obter_sessao_bd),
    usuario_atual: models.Usuario = Depends(obter_usuario_atual)
):
    item = db.query(models.Item).filter(
        models.Item.id == item_id,
        models.Item.id_dono == usuario_atual.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    db.delete(item)
    db.commit()
    return RedirectResponse(url="/itens", status_code=status.HTTP_303_SEE_OTHER)

