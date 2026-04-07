from database import obter_conexao


def _linha_para_dicionario(linha):
    """Converte um sqlite3.Row em dicionário Python."""
    return dict(linha) if linha else None


# Gêneros


def listar_generos():
    """Retorna todos os gêneros cadastrados, ordenados pelo nome."""
    conexao = obter_conexao()
    linhas = conexao.execute(
        "SELECT id, nome FROM generos ORDER BY nome"
    ).fetchall()
    conexao.close()
    return [_linha_para_dicionario(linha) for linha in linhas]


def cadastrar_genero(nome):
    """Insere um novo gênero. Retorna None se já existir (UNIQUE)."""
    conexao = obter_conexao()
    try:
        cursor = conexao.execute(
            "INSERT INTO generos (nome) VALUES (?)", (nome,)
        )
        conexao.commit()
        # Busca o registro recém-criado para retornar com o id gerado
        genero_criado = conexao.execute(
            "SELECT id, nome FROM generos WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return _linha_para_dicionario(genero_criado)
    except Exception:
        # Violação de UNIQUE — gênero já existe
        conexao.rollback()
        return None
    finally:
        conexao.close()


# Filmes


def listar_filmes(status=None, genero_id=None, busca=None):
    """Retorna filmes com filtros opcionais de status, genero_id e busca."""
    # WHERE 1=1 simplifica a concatenação dinâmica de condições
    sql = """
        SELECT f.id, f.titulo, f.ano, f.nota, f.status,
               f.comentario, f.data_cadastro,
               g.id   AS genero_id,
               g.nome AS genero_nome
        FROM filmes f
        LEFT JOIN generos g ON f.genero_id = g.id
        WHERE 1 = 1
    """
    parametros = []

    if status:
        sql += " AND f.status = ?"
        parametros.append(status)

    if genero_id:
        sql += " AND f.genero_id = ?"
        parametros.append(genero_id)

    if busca:
        sql += " AND f.titulo LIKE ?"
        parametros.append(f"%{busca}%")

    # Mais recentes primeiro
    sql += " ORDER BY f.data_cadastro DESC"

    conexao = obter_conexao()
    linhas = conexao.execute(sql, parametros).fetchall()
    conexao.close()

    return [_formatar_filme(linha) for linha in linhas]


def buscar_filme_por_id(filme_id):
    """Retorna um único filme pelo ID, ou None se não encontrado."""
    conexao = obter_conexao()
    linha = conexao.execute("""
        SELECT f.id, f.titulo, f.ano, f.nota, f.status,
               f.comentario, f.data_cadastro,
               g.id   AS genero_id,
               g.nome AS genero_nome
        FROM filmes f
        LEFT JOIN generos g ON f.genero_id = g.id
        WHERE f.id = ?
    """, (filme_id,)).fetchone()
    conexao.close()

    return _formatar_filme(linha) if linha else None


def cadastrar_filme(dados):
    """Insere um novo filme e retorna o registro criado."""
    conexao = obter_conexao()
    cursor = conexao.execute("""
        INSERT INTO filmes (titulo, ano, nota, status, comentario, genero_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        dados["titulo"],
        dados.get("ano"),
        dados.get("nota"),
        dados.get("status"),
        dados.get("comentario"),
        dados.get("genero_id"),
    ))
    conexao.commit()

    # Reutiliza buscar_filme_por_id para retornar o filme com gênero aninhado
    filme_criado = buscar_filme_por_id(cursor.lastrowid)
    conexao.close()
    return filme_criado


def atualizar_filme(filme_id, dados):
    """Atualiza somente os campos presentes em 'dados'."""
    # Whitelist de campos aceitos para evitar injeção de colunas inválidas
    campos_permitidos = ["titulo", "ano", "nota", "status", "comentario", "genero_id"]
    campos_para_atualizar = {
        campo: dados[campo]
        for campo in campos_permitidos
        if campo in dados
    }

    if not campos_para_atualizar:
        return buscar_filme_por_id(filme_id)

    # Monta SET dinâmico: "titulo = ?, ano = ?" com placeholders seguros
    clausula_set = ", ".join(f"{campo} = ?" for campo in campos_para_atualizar)
    valores = list(campos_para_atualizar.values()) + [filme_id]

    conexao = obter_conexao()
    conexao.execute(
        f"UPDATE filmes SET {clausula_set} WHERE id = ?", valores
    )
    conexao.commit()
    conexao.close()

    return buscar_filme_por_id(filme_id)


def remover_filme(filme_id):
    """Remove um filme pelo ID. Retorna True se removeu, False se não encontrou."""
    conexao = obter_conexao()
    resultado = conexao.execute(
        "DELETE FROM filmes WHERE id = ?", (filme_id,)
    )
    conexao.commit()
    linhas_afetadas = resultado.rowcount
    conexao.close()
    return linhas_afetadas > 0


# Estatísticas


def obter_estatisticas():
    """Retorna resumo do catálogo: total, média, distribuição e gênero favorito."""
    conexao = obter_conexao()

    resumo = conexao.execute("""
        SELECT COUNT(*) AS total_filmes,
               ROUND(AVG(nota), 1) AS media_notas
        FROM filmes
    """).fetchone()

    # Agrupa contagem por status (ignora filmes sem status definido)
    linhas_status = conexao.execute("""
        SELECT status, COUNT(*) AS quantidade
        FROM filmes
        WHERE status IS NOT NULL
        GROUP BY status
    """).fetchall()

    por_status = {linha["status"]: linha["quantidade"] for linha in linhas_status}

    # Gênero com mais filmes marcados como "assistido"
    genero_top = conexao.execute("""
        SELECT g.nome, COUNT(*) AS quantidade
        FROM filmes f
        JOIN generos g ON f.genero_id = g.id
        WHERE f.status = 'assistido'
        GROUP BY g.nome
        ORDER BY quantidade DESC
        LIMIT 1
    """).fetchone()

    conexao.close()

    return {
        "total_filmes": resumo["total_filmes"],
        "media_notas": resumo["media_notas"] or 0,
        "por_status": por_status,
        "genero_mais_assistido": (
            _linha_para_dicionario(genero_top) if genero_top else None
        ),
    }


def _formatar_filme(linha):
    """Transforma uma linha do JOIN filmes+generos no formato da API.

    Extrai genero_id e genero_nome da linha plana e os aninha em um
    objeto 'genero', mantendo a resposta consistente com o schema.
    """
    if linha is None:
        return None

    filme = dict(linha)
    genero_id = filme.pop("genero_id", None)
    genero_nome = filme.pop("genero_nome", None)

    filme["genero"] = (
        {"id": genero_id, "nome": genero_nome}
        if genero_id
        else None
    )

    return filme
