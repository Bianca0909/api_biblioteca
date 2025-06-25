# Biblioteca Pessoal API

API para gerenciar sua lista pessoal de livros, filmes e séries. Interface web com autenticação de usuários, gerenciamento de itens e funcionalidades de busca.

## Funcionalidades

- Autenticação de usuários com validação de email e senha
- Interface web responsiva usando Bootstrap 5
- Gerenciamento completo de itens (criar, editar, excluir)
- Busca por título de itens
- Suporte a tags e favoritos
- Avaliações de 1 a 5 estrelas
- Status de progresso (para ler, lendo, completado)

## Requisitos

- Python 3.12+
- FastAPI
- Uvicorn
- Pydantic
- SQLAlchemy
- PyJWT
- bcrypt
- email-validator
- Jinja2
- Bootstrap 5

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
  - Validação de email (formato válido)
  - Validação de senha (mínimo 8 caracteres, 1 maiúscula, 1 minúscula, 1 número)

- `POST /login`: Fazer login (cookie httponly)
- `GET /logout`: Fazer logout (limpa cookie de autenticação)

### Itens (Requer Autenticação)

Todas as rotas requerem cookie de autenticação válido

- `GET /itens`: Página de listagem de itens
  - Busca por título
  - Visualização em cards
  - Ações rápidas (editar/excluir)

- `GET /itens/criar`: Página de criação de item
- `POST /itens/criar`: Criar novo item
  - Título, tipo (livro/filme/série)
  - Status (para_ler/lendo/completado)
  - Descrição e avaliação
  - Tags e favorito

- `GET /itens/{id}/editar`: Página de edição
- `POST /itens/{id}/editar`: Atualizar item
- `POST /itens/{id}/deletar`: Remover item

## Interface Web

1. Página inicial (`/`)
   - Boas-vindas e status de autenticação
   - Link para login/registro

2. Autenticação
   - Login (`/login`)
   - Registro (`/registrar`)
   - Logout (`/logout`)

3. Gerenciamento de Itens
   - Listagem (`/itens`)
     - Cards com informações resumidas
     - Busca por título
     - Botões de ação (editar/excluir)
   
   - Criação (`/itens/criar`)
     - Formulário completo
     - Validação em tempo real
     - Preview antes de salvar

   - Edição (`/itens/{id}/editar`)
     - Mesmo formulário da criação
     - Dados pré-preenchidos

   - Detalhes (`/itens/{id}`)
     - Visualização completa
     - Todas as informações do item
