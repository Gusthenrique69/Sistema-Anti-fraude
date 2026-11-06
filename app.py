"""Menu interativo do Sistema Antifraude em Tempo Real.

    python antifraude/app.py
"""

from db import criar_estrutura, popular_dados_teste
from motor import (
    listar_clientes,
    listar_transferencias,
    processar_transferencia,
    resumo_por_status,
)

MENU = """
============================================
 SISTEMA ANTIFRAUDE EM TEMPO REAL
============================================
1 - Analisar uma nova transferencia
2 - Ver ultimas transferencias
3 - Ver resumo por status
4 - Ver clientes
5 - Recarregar dados de teste
0 - Sair
"""


def perguntar_int(texto: str) -> int:
    while True:
        try:
            return int(input(texto).strip())
        except ValueError:
            print("  Digite um numero valido.")


def analisar(conn):
    for c in listar_clientes(conn):
        print(f"  {c['id']} - {c['nome']} ({c['cidade_base']})")
    tx = {
        "cliente_id": perguntar_int("ID do cliente: "),
        "valor_centavos": int(round(float(input("Valor em R$: ").replace(",", ".")) * 100)),
        "cidade": input("Cidade da transacao: ").strip(),
        "dispositivo_id": input("ID do aparelho: ").strip(),
        "conta_destino": input("Conta de destino: ").strip(),
    }
    r = processar_transferencia(conn, tx)
    print(f"\n  Score de risco: {r['score']}  ->  {r['status'].upper()}")
    for regra, pontos, detalhe in r["alertas"]:
        print(f"  - {regra} (+{pontos}): {detalhe}")
    if not r["alertas"]:
        print("  Nenhuma regra disparou.")


def main():
    conn = criar_estrutura()
    try:
        while True:
            print(MENU)
            opcao = input("Escolha: ").strip()
            if opcao == "1":
                analisar(conn)
            elif opcao == "2":
                for t in listar_transferencias(conn):
                    print(
                        f"  #{t['id']:<4} {t['cliente']:<18} R$ {float(t['valor_reais']):>9.2f} "
                        f"{t['cidade']:<16} score {t['score_risco']:>3} {t['status']}"
                    )
            elif opcao == "3":
                for linha in resumo_por_status(conn):
                    print(
                        f"  {linha['status']:<15} {linha['total']} "
                        f"(score medio {float(linha['score_medio']):.1f})"
                    )
            elif opcao == "4":
                for c in listar_clientes(conn):
                    print(f"  {c['id']} - {c['nome']} ({c['cidade_base']})")
            elif opcao == "5":
                popular_dados_teste(conn)
                print("  Dados de teste recarregados.")
            elif opcao == "0":
                break
            else:
                print("  Opcao invalida.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
