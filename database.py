import os
import sqlite3

# Caminho absoluto do banco, relativo ao diretório deste arquivo
CAMINHO_BANCO = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "instance",
    "datafilmes.db",
)


def obter_conexao():
    """Cria e retorna uma conexão com o banco SQLite."""
    conexao = sqlite3.connect(CAMINHO_BANCO)
    # Row permite acessar colunas por nome (dict-like)
    conexao.row_factory = sqlite3.Row
    # Habilita enforcement de chaves estrangeiras (desativado por padrão no SQLite)
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def inicializar_banco():
    """Cria as tabelas 'generos' e 'filmes' caso ainda não existam."""
    # Garante que o diretório instance/ existe antes de criar o .db
    os.makedirs(os.path.dirname(CAMINHO_BANCO), exist_ok=True)

    conexao = obter_conexao()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS generos (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT    NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS filmes (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo         TEXT    NOT NULL,
            ano            INTEGER,
            nota           REAL    CHECK (nota >= 0 AND nota <= 5),
            status         TEXT    CHECK (status IN ('quero_ver', 'assistindo', 'assistido')),
            comentario     TEXT,
            data_cadastro  TEXT    NOT NULL DEFAULT (datetime('now')),
            genero_id      INTEGER,
            FOREIGN KEY (genero_id) REFERENCES generos (id)
        )
    """)

    conexao.commit()
    conexao.close()
