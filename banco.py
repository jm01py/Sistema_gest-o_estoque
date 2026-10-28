
import sqlite3
from pathlib import Path

CAMINHO_BANCO = Path(__file__).resolve().parent / "estoque.db"


def conectar():
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def criar_banco():
    with conectar() as conexao:
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL UNIQUE,
                nome TEXT NOT NULL,
                categoria TEXT,
                preco_compra REAL NOT NULL DEFAULT 0
                    CHECK (preco_compra >= 0),
                preco_venda REAL NOT NULL DEFAULT 0
                    CHECK (preco_venda >= 0),
                quantidade INTEGER NOT NULL DEFAULT 0
                    CHECK (quantidade >= 0),
                estoque_minimo INTEGER NOT NULL DEFAULT 5
                    CHECK (estoque_minimo >= 0)
            )
        """)

        conexao.execute("""
            CREATE TABLE IF NOT EXISTS movimentacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER NOT NULL,
                tipo TEXT NOT NULL
                    CHECK (tipo IN ('ENTRADA', 'SAIDA')),
                quantidade INTEGER NOT NULL
                    CHECK (quantidade > 0),
                data TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                observacao TEXT,
                FOREIGN KEY (produto_id)
                    REFERENCES produtos(id)
            )
        """)

    print("Banco de dados preparado com sucesso!")


if __name__ == "__main__":
    criar_banco()
