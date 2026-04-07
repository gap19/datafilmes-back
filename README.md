# DataFilmes — API

API REST para catálogo pessoal de filmes, desenvolvida em Python com Flask e documentada automaticamente com OpenAPI 3 (Swagger).

## Tecnologias

- Python 3
- Flask 3.1.0
- Flask-OpenAPI3 4.3.1
- Pydantic 2.12.5
- SQLite3
- Flask-CORS 5.0.1

## Estrutura do projeto

```
datafilmes-back/
├── app.py              # Rotas, schemas Pydantic e configuração da API
├── database.py         # Conexão e inicialização do banco SQLite
├── models.py           # Operações CRUD e consultas ao banco
├── requirements.txt    # Dependências Python
└── instance/
    └── datafilmes.db   # Banco de dados (criado automaticamente)
```

## Instalação e execução

### Pré-requisitos

- Python 3.10 ou superior
- pip

### Passos

```bash
# 1. Instale as dependências
pip install -r requirements.txt

# 2. Inicie o servidor
python app.py
```

O servidor inicia em `http://localhost:5000`.

A documentação interativa da API (Swagger UI) fica disponível em `http://localhost:5000/openapi`.

## Rotas da API

| Método | Endpoint           | Descrição                        |
|--------|--------------------|----------------------------------|
| GET    | `/generos`         | Lista todos os gêneros           |
| POST   | `/genero`          | Cadastra um gênero               |
| GET    | `/filmes`          | Lista filmes (com filtros)       |
| POST   | `/filme`           | Cadastra um filme                |
| GET    | `/filme/<id>`      | Busca filme por ID               |
| PATCH  | `/filme/<id>`      | Atualiza parcialmente um filme   |
| DELETE | `/filme/<id>`      | Remove um filme                  |
| GET    | `/estatisticas`    | Retorna estatísticas do catálogo |

### Filtros disponíveis em `GET /filmes`

| Parâmetro   | Tipo    | Descrição                                |
|-------------|---------|------------------------------------------|
| `status`    | string  | `quero_ver`, `assistindo` ou `assistido` |
| `genero_id` | integer | ID do gênero                             |
| `busca`     | string  | Busca parcial no título                  |

## Banco de dados

O SQLite cria o arquivo `instance/datafilmes.db` automaticamente na primeira execução. Duas tabelas são criadas:

- **generos** — `id`, `nome` (único)
- **filmes** — `id`, `titulo`, `ano`, `nota` (0–5), `status`, `comentario`, `data_cadastro`, `genero_id` (FK → generos)
