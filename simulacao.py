"""Roda os cenarios de teste do sistema antifraude.

    python antifraude/simulacao.py
"""

from db import criar_estrutura, popular_dados_teste
from motor import processar_transferencia, resumo_por_status


CENARIOS = [
    (
        "Caso 1 - Compra normal",
        {
            "cliente_id": 1,
            "valor_centavos": 3000,
            "cidade": "São Paulo",
            "dispositivo_id": "celular-rodrigo",
            "conta_destino": "mercearia-esquina",
        },
    ),
    (
        "Caso 2 - Suspeita (outra cidade + valor alto + aparelho novo)",
        {
            "cliente_id": 1,
            "valor_centavos": 50000,
            "cidade": "Rio de Janeiro",
            "dispositivo_id": "celular-desconhecido",
            "conta_destino": "usuario-aleatorio",
        },
    ),
    (
        "Caso 3 - Fraude confirmada (conta na lista negra)",
        {
            "cliente_id": 1,
            "valor_centavos": 1000,
            "cidade": "São Paulo",
            "dispositivo_id": "celular-rodrigo",
            "conta_destino": "conta-fraude-999",
        },
    ),
]

ICONES = {"aprovada": "OK ", "revisao_manual": "!! ", "bloqueada": "XX "}


def main():
    conexao = criar_estrutura()
    try:
        popular_dados_teste(conexao)
        print("Banco pronto e populado com dados de teste.\n")
        print("--- SIMULACOES EM TEMPO REAL ---\n")

        for titulo, tx in CENARIOS:
            r = processar_transferencia(conexao, tx)
            print(f"{ICONES[r['status']]}{titulo}")
            print(f"    Score de risco: {r['score']}  ->  {r['status'].upper()}")
            for regra, pontos, detalhe in r["alertas"]:
                print(f"    - {regra} (+{pontos}): {detalhe}")
            print()

        print("--- RESUMO NO BANCO ---")
        for linha in resumo_por_status(conexao):
            print(
                f"  {linha['status']:<15} {linha['total']} transferencia(s), "
                f"score medio {float(linha['score_medio']):.1f}"
            )
    finally:
        conexao.close()


if __name__ == "__main__":
    main()
