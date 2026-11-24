"""Acesso ao banco SQLite."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PADRAO = Path(__file__).parent / "gastos.db"


def caminho_db():
    """Caminho do banco; pode ser trocado pela variável de ambiente DB_PATH."""
    return Path(os.environ.get("DB_PATH") or DB_PADRAO)


@contextmanager
def conectar():
    conn = sqlite3.connect(caminho_db())
    conn.row_factory = sqlite3.Row
    try:
        with conn:  # commit automático (ou rollback em caso de erro)
            yield conn
    finally:
        conn.close()


def init_db():
    with conectar() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS gastos (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                numero    TEXT NOT NULL,
                item      TEXT NOT NULL,
                valor     REAL NOT NULL,
                categoria TEXT NOT NULL DEFAULT 'Outros',
                criado_em TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
            """
        )
        # Migração: bancos criados antes de existir a coluna "categoria"
        colunas = {linha["name"] for linha in conn.execute("PRAGMA table_info(gastos)")}
        if "categoria" not in colunas:
            conn.execute(
                "ALTER TABLE gastos ADD COLUMN categoria TEXT NOT NULL DEFAULT 'Outros'"
            )


def adicionar_gasto(numero, item, valor, categoria="Outros"):
    with conectar() as conn:
        conn.execute(
            "INSERT INTO gastos (numero, item, valor, categoria) VALUES (?, ?, ?, ?)",
            (numero, item, round(valor, 2), categoria),
        )


def ultimos_gastos(numero, limite=5):
    with conectar() as conn:
        return conn.execute(
            "SELECT id, item, valor, categoria, criado_em FROM gastos "
            "WHERE numero = ? ORDER BY id DESC LIMIT ?",
            (numero, limite),
        ).fetchall()


def total_do_mes(numero):
    with conectar() as conn:
        linha = conn.execute(
            "SELECT COALESCE(SUM(valor), 0) AS total FROM gastos "
            "WHERE numero = ? "
            "AND strftime('%Y-%m', criado_em) = strftime('%Y-%m', 'now', 'localtime')",
            (numero,),
        ).fetchone()
        return linha["total"]


def total_por_categoria(numero):
    """Total do mês atual agrupado por categoria, do maior para o menor."""
    with conectar() as conn:
        return conn.execute(
            "SELECT categoria, SUM(valor) AS total FROM gastos "
            "WHERE numero = ? "
            "AND strftime('%Y-%m', criado_em) = strftime('%Y-%m', 'now', 'localtime') "
            "GROUP BY categoria ORDER BY total DESC",
            (numero,),
        ).fetchall()


def apagar_ultimo(numero):
    """Apaga o último gasto do número e devolve (item, valor), ou None."""
    with conectar() as conn:
        linha = conn.execute(
            "SELECT id, item, valor FROM gastos WHERE numero = ? ORDER BY id DESC LIMIT 1",
            (numero,),
        ).fetchone()
        if linha is None:
            return None
        conn.execute("DELETE FROM gastos WHERE id = ?", (linha["id"],))
        return linha["item"], linha["valor"]


def listar_para_exportar(mes=None):
    """Todos os gastos (ou só os de um mês 'AAAA-MM'), do mais antigo ao mais novo."""
    consulta = "SELECT id, criado_em, item, categoria, valor FROM gastos"
    parametros = ()
    if mes:
        consulta += " WHERE strftime('%Y-%m', criado_em) = ?"
        parametros = (mes,)
    consulta += " ORDER BY criado_em, id"
    with conectar() as conn:
        return conn.execute(consulta, parametros).fetchall()
