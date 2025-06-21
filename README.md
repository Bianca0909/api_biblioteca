# Biblioteca Pessoal API

API para gerenciar sua lista pessoal de livros, filmes e séries. Inclui autenticação de usuários e proteção de rotas.

## Requisitos

- Python 3.8+
- FastAPI
- Uvicorn
- Pydantic
- SQLAlchemy
- PyJWT
- bcrypt
- email-validator

## Instalação

1. Clone o repositório
2. Entre na pasta do projeto:
```bash
cd api-biblioteca
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Executando a API

```bash
uvicorn src.main:app --reload
```

A API estará disponível em `http://localhost:8000`

Documentação Swagger UI: `http://localhost:8000/docs`

## Endpoints

### Autenticação

- `POST /registrar`: Registrar novo usuário
  ```bash
  curl -X POST "http://localhost:8000/registrar" -H "Content-Type: application/json" -d '{
    "email": "usuario@exemplo.com",
    "nome_usuario": "usuario",
    "senha": "senha123"
  }'
  ```

- `POST /login`: Fazer login e obter token de acesso
  ```bash
  curl -X POST "http://localhost:8000/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=usuario@exemplo.com&password=senha123"
  ```

### Itens (Requer Autenticação)

Todas as rotas de itens requerem o token de acesso no header `Authorization: Bearer <token>`

- `POST /itens`: Adicionar novo item (livro/filme/série)
- `GET /itens`: Listar todos os itens
  - Filtros opcionais:
    - `type`: Filtrar por tipo (book/movie/series)
    - `status`: Filtrar por status (to_read/reading/completed)
    - `tag`: Filtrar por tag específica
    - `favourite`: Filtrar por favoritos (true/false)
- `GET /itens/{id}`: Ver detalhes de um item específico
- `PUT /itens/{id}`: Atualizar um item
- `DELETE /itens/{id}`: Remover um item

### Exemplos de Uso

#### 1. Registrar um novo usuário:
```bash
curl -X POST "http://localhost:8000/registrar" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@exemplo.com",
    "nome_usuario": "usuario",
    "senha": "senha123"
  }'
```

#### 2. Fazer login e obter token:
```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=usuario@exemplo.com&password=senha123"
```

#### 3. Adicionar um novo item (com token):
```bash
curl -X POST "http://localhost:8000/itens" \
  -H "Authorization: Bearer seu_token_aqui" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "O Senhor dos Anéis",
    "tipo": "livro",
    "status": "lendo",
    "descricao": "Trilogia épica de fantasia",
    "avaliacao": 5,
    "tags": ["fantasia", "aventura", "clássico"],
    "favorito": true
  }'
```

#### 4. Exemplos de Filtros (com token)

```bash
# Listar apenas livros
curl "http://localhost:8000/itens?tipo=livro" \
  -H "Authorization: Bearer seu_token_aqui"

# Listar itens com tag específica
curl "http://localhost:8000/itens?tag=fantasia" \
  -H "Authorization: Bearer seu_token_aqui"

# Listar favoritos
curl "http://localhost:8000/itens?favorito=true" \
  -H "Authorization: Bearer seu_token_aqui"

# Listar itens em leitura/andamento
curl "http://localhost:8000/itens?status=lendo" \
  -H "Authorization: Bearer seu_token_aqui"
```
