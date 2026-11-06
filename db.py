"""Conexao com o MySQL e criacao automatica do banco/tabelas."""

import os
import pathlib

import pymysql
from pymysql.cursors import DictCursor

try:  # carrega o arquivo .env, se existir
    from dotenv import load_dotenv

    load_dotenv(pathlib.Path(__file__).with_name(".env"))
except ImportError:  # pragma: no cover
    pass

PASTA = pathlib.Path(__file__).parent
SCHEMA_SQL = PASTA / "schema.sql"
SEED_SQL = PASTA / "seed.sql"


def config():
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", "3306")),
        "user": os.environ.get("DB_USER", "root"),
        "password": os.environ.get("DB_PASSWORD", ""),
        "charset": "utf8mb4",
    }


def conectar(com_banco: bool = True):
    """Abre uma conexao com o MySQL."""
    parametros = config()
    if com_banco:
        parametros["database"] = os.environ.get("DB_NAME", "antifraude")
    return pymysql.connect(cursorclass=DictCursor, autocommit=False, **parametros)


def _executar_arquivo(conn, caminho: pathlib.Path) -> None:
    """Executa um .sql comando a comando (pymysql nao aceita varios de uma vez)."""
    sql = caminho.read_text(encoding="utf-8")
    linhas = [l for l in sql.splitlines() if not l.strip().startswith("--")]
    for comando in "\n".join(linhas).split(";"):
        comando = comando.strip()
        if comando:
            with conn.cursor() as cursor:
                cursor.execute(comando)
    conn.commit()


def criar_estrutura():
    """Garante que o banco e as tabelas existem. Retorna a conexao pronta."""
    temporaria = pymysql.connect(autocommit=True, **config())
    with temporaria.cursor() as cursor:
        cursor.execute(
            "CREATE DATABASE IF NOT EXISTS antifraude "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
    temporaria.close()

    conn = conectar()
    _executar_arquivo(conn, SCHEMA_SQL)
    return conn


def popular_dados_teste(conn) -> None:
    """Apaga tudo e recarrega os dados de exemplo do seed.sql."""
    _executar_arquivo(conn, SEED_SQL)
