
import sqlite3
from pathlib import Path

CAMINHO_BANCO = Path(__file__).resolve().parent / "estoque.db"


def conectar():
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def cadastrar_produto():
    print("\n--- CADASTRO DE PRODUTO ---")

    codigo = input("Código: ").strip()
    nome = input("Nome: ").strip()
    categoria = input("Categoria: ").strip()

    preco_compra = float(input("Preço de compra: "))
    preco_venda = float(input("Preço de venda: "))
    quantidade = int(input("Quantidade inicial: "))
    estoque_minimo = int(input("Estoque mínimo: "))

    if not codigo or not nome:
        print("Código e nome são obrigatórios.")
        return

    if (preco_compra < 0 or preco_venda < 0
            or quantidade < 0 or estoque_minimo < 0):
        print("Os valores não podem ser negativos.")
        return

    with conectar() as conexao:
        cursor = conexao.execute("""
            INSERT INTO produtos
            (codigo, nome, categoria, preco_compra,
             preco_venda, quantidade, estoque_minimo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            codigo, nome, categoria, preco_compra,
            preco_venda, quantidade, estoque_minimo
        ))

        produto_id = cursor.lastrowid

        if quantidade > 0:
            conexao.execute("""
                INSERT INTO movimentacoes
                (produto_id, tipo, quantidade, observacao)
                VALUES (?, 'ENTRADA', ?, ?)
            """, (
                produto_id, quantidade, "Estoque inicial"
            ))

    print("Produto cadastrado com sucesso!")


def listar_produtos():
    with conectar() as conexao:
        produtos = conexao.execute("""
            SELECT id, codigo, nome, quantidade,
                   estoque_minimo, preco_venda
            FROM produtos
            ORDER BY nome
        """).fetchall()

    print("\n--- ESTOQUE ATUAL ---")

    if not produtos:
        print("Nenhum produto cadastrado.")
        return

    for p in produtos:
        alerta = (
            " [ESTOQUE BAIXO]"
            if p[3] <= p[4] else ""
        )

        print(
            f"ID: {p[0]} | Código: {p[1]} | "
            f"Produto: {p[2]} | Quantidade: {p[3]} | "
            f"Preço: R$ {p[5]:.2f}{alerta}"
        )


def movimentar_estoque(tipo):
    print(f"\n--- REGISTRAR {tipo} ---")

    try:
        produto_id = int(input("ID do produto: "))
        quantidade = int(input("Quantidade: "))
    except ValueError:
        print("Informe IDs e quantidades em números inteiros.")
        return

    if quantidade <= 0:
        print("A quantidade deve ser maior que zero.")
        return

    observacao = input("Observação (opcional): ").strip()

    conexao = conectar()

    try:
     
        conexao.execute("BEGIN IMMEDIATE")

        produto = conexao.execute("""
            SELECT nome, quantidade
            FROM produtos
            WHERE id = ?
        """, (produto_id,)).fetchone()

        if produto is None:
            print("Produto não encontrado.")
            conexao.rollback()
            return

        nome, saldo_atual = produto

        if tipo == "SAIDA" and quantidade > saldo_atual:
            print(
                f"Estoque insuficiente! Disponível: "
                f"{saldo_atual} unidade(s)."
            )
            conexao.rollback()
            return

        if tipo == "ENTRADA":
            nova_quantidade = saldo_atual + quantidade
        else:
            nova_quantidade = saldo_atual - quantidade

        conexao.execute("""
            UPDATE produtos
            SET quantidade = ?
            WHERE id = ?
        """, (nova_quantidade, produto_id))

        conexao.execute("""
            INSERT INTO movimentacoes
            (produto_id, tipo, quantidade, observacao)
            VALUES (?, ?, ?, ?)
        """, (produto_id, tipo, quantidade, observacao))

        conexao.commit()

        print(f"{tipo.capitalize()} registrada com sucesso!")
        print(f"Produto: {nome}")
        print(f"Estoque anterior: {saldo_atual}")
        print(f"Estoque atual: {nova_quantidade}")

    except sqlite3.Error as erro:
        conexao.rollback()
        print(f"Erro no banco de dados: {erro}")

    finally:
        conexao.close()


def consultar_historico():
    with conectar() as conexao:
        registros = conexao.execute("""
            SELECT m.id, p.nome, m.tipo,
                   m.quantidade, m.data, m.observacao
            FROM movimentacoes m
            JOIN produtos p ON p.id = m.produto_id
            ORDER BY m.id DESC
        """).fetchall()

    print("\n--- HISTÓRICO DE MOVIMENTAÇÕES ---")

    if not registros:
        print("Nenhuma movimentação registrada.")
        return

    for r in registros:
        print(
            f"Movimentação: {r[0]} | Produto: {r[1]} | "
            f"Tipo: {r[2]} | Quantidade: {r[3]} | "
            f"Data: {r[4]} | Observação: {r[5] or '-'}"
        )


def menu():
    while True:
        print("\n===== GESTÃO DE ESTOQUE =====")
        print("1 - Cadastrar produto")
        print("2 - Listar produtos")
        print("3 - Registrar entrada")
        print("4 - Registrar saída")
        print("5 - Consultar histórico")
        print("0 - Sair")

        opcao = input("Escolha uma opção: ").strip()

        try:
            if opcao == "1":
                cadastrar_produto()
            elif opcao == "2":
                listar_produtos()
            elif opcao == "3":
                movimentar_estoque("ENTRADA")
            elif opcao == "4":
                movimentar_estoque("SAIDA")
            elif opcao == "5":
                consultar_historico()
            elif opcao == "0":
                print("Sistema encerrado.")
                break
            else:
                print("Opção inválida.")

        except ValueError:
            print("Valor inválido. Confira os dados digitados.")
        except sqlite3.IntegrityError as erro:
            print(
                "Não foi possível salvar. "
                "Verifique se o código já existe e se os dados são válidos."
            )


if __name__ == "__main__":

    from banco import criar_banco
    criar_banco()
    menu()
