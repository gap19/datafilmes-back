from flask import jsonify
from flask_cors import CORS
from flask_openapi3 import OpenAPI, Info, Tag
from pydantic import BaseModel, Field, RootModel, ValidationError
from typing import Literal, Optional, List

from database import inicializar_banco
from models import (
    cadastrar_genero,
    listar_generos,
    cadastrar_filme,
    listar_filmes,
    buscar_filme_por_id,
    atualizar_filme,
    remover_filme,
    obter_estatisticas,
)


def tratar_erro_validacao(e: ValidationError):
    """Callback global: converte erros do Pydantic em resposta JSON 422."""
    mensagens = "; ".join(err["msg"] for err in e.errors())
    resposta = jsonify({"erro": f"Dados inválidos: {mensagens}"})
    resposta.status_code = 422
    return resposta


# Configuração da aplicação

info = Info(
    title="DataFilmes API",
    version="1.0.0",
    description="API REST para catálogo pessoal de filmes.",
)
app = OpenAPI(__name__, info=info, validation_error_callback=tratar_erro_validacao)
CORS(app)  # Permite requisições cross-origin do frontend

STATUS_VALIDOS = ("quero_ver", "assistindo", "assistido")

# Tags agrupam endpoints na documentação Swagger gerada automaticamente
tag_generos = Tag(name="Gêneros", description="Operações com gêneros")
tag_filmes = Tag(name="Filmes", description="Operações com filmes")
tag_estatisticas = Tag(name="Estatísticas", description="Estatísticas do catálogo")


# Schemas Pydantic
# Definem validação de entrada e geram o schema OpenAPI automaticamente


StatusType = Literal["quero_ver", "assistindo", "assistido"]


class GeneroBody(BaseModel):
    model_config = {"json_schema_extra": {"example": {"nome": "Ficção Científica"}}}

    nome: str = Field(..., description="Nome do gênero")


class GeneroOut(BaseModel):
    id: int = Field(..., examples=[1])
    nome: str = Field(..., examples=["Ação"])


class FilmeQuery(BaseModel):
    """Parâmetros de query string para filtrar a listagem de filmes."""
    status: Optional[StatusType] = Field(None, description="Filtra por status")
    genero_id: Optional[int] = Field(None, description="Filtra pelo ID do gênero")
    busca: Optional[str] = Field(None, description="Busca parcial no título")


class FilmePath(BaseModel):
    filme_id: int = Field(..., description="ID do filme")


class FilmeBody(BaseModel):
    """Corpo para criação de filme — título é obrigatório, demais campos opcionais."""
    model_config = {"json_schema_extra": {"example": {
        "titulo": "Interestelar",
        "ano": 2014,
        "nota": 4.5,
        "status": "assistido",
        "comentario": "Obra-prima do Nolan.",
        "genero_id": 1,
    }}}

    titulo: str = Field(..., description="Título do filme")
    ano: Optional[int] = Field(None, description="Ano de lançamento")
    nota: Optional[float] = Field(None, ge=0, le=5, description="Nota de 0 a 5")
    status: Optional[StatusType] = Field(None, description="quero_ver, assistindo ou assistido")
    comentario: Optional[str] = Field(None, description="Comentário pessoal sobre o filme")
    genero_id: Optional[int] = Field(None, description="ID numérico do gênero (consulte GET /generos)")


class FilmeUpdateBody(BaseModel):
    """Corpo para atualização parcial — todos os campos são opcionais."""
    model_config = {"json_schema_extra": {"example": {
        "titulo": "Interestelar",
        "ano": 2014,
        "nota": 5.0,
        "status": "assistido",
        "comentario": "Obra-prima do Nolan.",
        "genero_id": 1,
    }}}

    titulo: Optional[str] = Field(None, description="Título do filme")
    ano: Optional[int] = Field(None, description="Ano de lançamento")
    nota: Optional[float] = Field(None, ge=0, le=5, description="Nota de 0 a 5")
    status: Optional[StatusType] = Field(None, description="quero_ver, assistindo ou assistido")
    comentario: Optional[str] = Field(None, description="Comentário pessoal sobre o filme")
    genero_id: Optional[int] = Field(None, description="ID numérico do gênero (consulte GET /generos)")


class GeneroAninhado(BaseModel):
    id: int
    nome: str


class FilmeOut(BaseModel):
    """Representação de um filme na resposta da API, com gênero aninhado."""
    id: int
    titulo: str
    ano: Optional[int] = None
    nota: Optional[float] = None
    status: Optional[str] = None
    comentario: Optional[str] = None
    data_cadastro: str
    genero: Optional[GeneroAninhado] = None


class EstatisticasOut(BaseModel):
    total_filmes: int = Field(..., examples=[15])
    media_notas: float = Field(..., examples=[3.8])
    por_status: dict = Field(..., examples=[{"quero_ver": 3, "assistindo": 2, "assistido": 10}])
    genero_mais_assistido: Optional[dict] = Field(None, examples=[{"nome": "Ação", "quantidade": 5}])


class ErroOut(BaseModel):
    erro: str


class MensagemOut(BaseModel):
    mensagem: str


# Modelos de resposta para listagens (gera o formato de array na documentação)
class ListaGenerosOut(RootModel):
    root: List[GeneroOut]


class ListaFilmesOut(RootModel):
    root: List[FilmeOut]


# Rotas: Gêneros


@app.get("/generos", tags=[tag_generos], responses={200: ListaGenerosOut})
def rota_listar_generos():
    """Lista todos os gêneros cadastrados."""
    generos = listar_generos()
    return generos, 200


@app.post("/genero", tags=[tag_generos], responses={201: GeneroOut, 400: ErroOut, 409: ErroOut})
def rota_cadastrar_genero(body: GeneroBody):
    """Cadastra um novo gênero."""
    nome = body.nome.strip()

    if not nome:
        return {"erro": "O campo 'nome' é obrigatório."}, 400

    genero = cadastrar_genero(nome)

    # None indica violação de UNIQUE (gênero já existe)
    if genero is None:
        return {"erro": f"O gênero '{nome}' já está cadastrado."}, 409

    return genero, 201


# Rotas: Filmes


@app.get("/filmes", tags=[tag_filmes], responses={200: ListaFilmesOut})
def rota_listar_filmes(query: FilmeQuery):
    """Lista filmes com filtros opcionais."""
    filmes = listar_filmes(
        status=query.status,
        genero_id=query.genero_id,
        busca=query.busca,
    )
    return filmes, 200


@app.post("/filme", tags=[tag_filmes], responses={201: FilmeOut, 400: ErroOut})
def rota_cadastrar_filme(body: FilmeBody):
    """Cadastra um novo filme no catálogo."""
    # exclude_none evita enviar campos não preenchidos para o banco
    dados = body.model_dump(exclude_none=True)

    titulo = dados.get("titulo", "").strip()
    if not titulo:
        return {"erro": "O campo 'titulo' é obrigatório."}, 400

    dados["titulo"] = titulo
    filme = cadastrar_filme(dados)
    return filme, 201


@app.get("/filme/<int:filme_id>", tags=[tag_filmes], responses={200: FilmeOut, 404: ErroOut})
def rota_buscar_filme(path: FilmePath):
    """Busca um filme pelo seu ID."""
    filme = buscar_filme_por_id(path.filme_id)

    if filme is None:
        return {"erro": "Filme não encontrado."}, 404

    return filme, 200


@app.put("/filme/<int:filme_id>", tags=[tag_filmes], responses={200: FilmeOut, 400: ErroOut, 404: ErroOut})
def rota_atualizar_filme(path: FilmePath, body: FilmeUpdateBody):
    """Atualiza dados de um filme existente."""
    # Verifica existência antes de tentar atualizar
    filme_existente = buscar_filme_por_id(path.filme_id)
    if filme_existente is None:
        return {"erro": "Filme não encontrado."}, 404

    dados = body.model_dump(exclude_none=True)
    filme_atualizado = atualizar_filme(path.filme_id, dados)
    return filme_atualizado, 200


@app.delete("/filme/<int:filme_id>", tags=[tag_filmes], responses={200: MensagemOut, 404: ErroOut})
def rota_remover_filme(path: FilmePath):
    """Remove um filme do catálogo."""
    removido = remover_filme(path.filme_id)

    if not removido:
        return {"erro": "Filme não encontrado."}, 404

    return {"mensagem": "Filme removido com sucesso."}, 200


# Rotas: Estatísticas


@app.get("/estatisticas", tags=[tag_estatisticas], responses={200: EstatisticasOut})
def rota_estatisticas():
    """Retorna estatísticas gerais do catálogo."""
    estatisticas = obter_estatisticas()
    return estatisticas, 200


# Main


if __name__ == "__main__":
    inicializar_banco()
    app.run(debug=True, port=5000)
