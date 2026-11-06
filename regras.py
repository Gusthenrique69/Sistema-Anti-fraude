"""Regras do motor antifraude.

Cada regra recebe a conexao e a transferencia e devolve uma lista de
alertas: (nome_da_regra, pontos, detalhe).
Somando os pontos temos o SCORE DE RISCO de 0 a 100.
"""

import datetime

LIMITE_APROVACAO = 30      # score <= 30  -> aprovada
LIMITE_REVISAO = 70        # score <= 70  -> revisao manual, acima -> bloqueada

JANELA_VELOCIDADE_MIN = 5  # minutos analisados na regra de velocidade
MAX_TX_NA_JANELA = 3       # a partir disso e considerado suspeito
MULTIPLICADOR_VALOR = 3    # valor acima de 3x a media historica


def regra_lista_negra(conn, tx):
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT motivo FROM lista_negra_contas WHERE conta_destino = %s",
            (tx["conta_destino"],),
        )
        linha = cursor.fetchone()
    if linha:
        return [("lista_negra", 100, linha["motivo"] or "Conta bloqueada")]
    return []


def regra_localizacao(conn, tx):
    with conn.cursor() as cursor:
        cursor.execute("SELECT cidade_base FROM clientes WHERE id = %s", (tx["cliente_id"],))
        cliente = cursor.fetchone()
    if cliente and tx["cidade"] != cliente["cidade_base"]:
        return [(
            "localizacao_divergente",
            40,
            f"Cidade base {cliente['cidade_base']}, transacao em {tx['cidade']}",
        )]
    return []


def regra_velocidade(conn, tx):
    desde = datetime.datetime.now() - datetime.timedelta(minutes=JANELA_VELOCIDADE_MIN)
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) AS total FROM transferencias "
            "WHERE cliente_id = %s AND data_hora >= %s",
            (tx["cliente_id"], desde),
        )
        total = cursor.fetchone()["total"]
    if total >= MAX_TX_NA_JANELA:
        return [(
            "velocidade",
            35,
            f"{total} transferencias em {JANELA_VELOCIDADE_MIN} minutos",
        )]
    return []


def regra_valor_atipico(conn, tx):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT AVG(valor_centavos) AS media FROM (
                SELECT valor_centavos FROM transferencias
                WHERE cliente_id = %s
                ORDER BY data_hora DESC
                LIMIT 10
            ) AS ultimas
            """,
            (tx["cliente_id"],),
        )
        media = cursor.fetchone()["media"]
    media = float(media) if media else 0.0
    if media > 0 and tx["valor_centavos"] > media * MULTIPLICADOR_VALOR:
        return [(
            "valor_atipico",
            25,
            f"R$ {tx['valor_centavos'] / 100:.2f} contra media de R$ {media / 100:.2f}",
        )]
    return []


def regra_dispositivo_novo(conn, tx):
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) AS total FROM transferencias "
            "WHERE cliente_id = %s AND dispositivo_id = %s",
            (tx["cliente_id"], tx["dispositivo_id"]),
        )
        conhecido = cursor.fetchone()["total"]
    if conhecido == 0:
        return [("dispositivo_novo", 20, f"Primeiro uso de {tx['dispositivo_id']}")]
    return []


def regra_madrugada(conn, tx):
    hora = datetime.datetime.now().hour
    if 0 <= hora < 5 and tx["valor_centavos"] >= 100000:
        return [("horario_incomum", 15, f"Transferencia alta as {hora}h")]
    return []


REGRAS = [
    regra_lista_negra,
    regra_localizacao,
    regra_velocidade,
    regra_valor_atipico,
    regra_dispositivo_novo,
    regra_madrugada,
]


def avaliar(conn, tx):
    """Roda todas as regras e devolve (score, lista_de_alertas)."""
    negra = regra_lista_negra(conn, tx)
    if negra:  # lista negra bloqueia na hora
        return 100, negra

    alertas = []
    for regra in REGRAS:
        if regra is regra_lista_negra:
            continue
        alertas.extend(regra(conn, tx))

    score = min(sum(pontos for _, pontos, _ in alertas), 100)
    return score, alertas


def classificar(score: int) -> str:
    if score <= LIMITE_APROVACAO:
        return "aprovada"
    if score <= LIMITE_REVISAO:
        return "revisao_manual"
    return "bloqueada"
