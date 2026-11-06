"""Motor antifraude: avalia, grava a transferencia e registra os alertas."""

from regras import avaliar, classificar


def processar_transferencia(conn, tx):
    """Avalia uma transferencia, grava no banco e devolve o resultado."""
    score, alertas = avaliar(conn, tx)
    status = classificar(score)

    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO transferencias
                (cliente_id, valor_centavos, cidade, dispositivo_id,
                 conta_destino, score_risco, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                tx["cliente_id"],
                tx["valor_centavos"],
                tx["cidade"],
                tx["dispositivo_id"],
                tx["conta_destino"],
                score,
                status,
            ),
        )
        transferencia_id = cursor.lastrowid

        for regra, pontos, detalhe in alertas:
            cursor.execute(
                """
                INSERT INTO alertas_fraude (transferencia_id, regra, pontos, detalhe)
                VALUES (%s, %s, %s, %s)
                """,
                (transferencia_id, regra, pontos, detalhe),
            )

    conn.commit()
    return {
        "id": transferencia_id,
        "score": score,
        "status": status,
        "alertas": alertas,
    }


def listar_transferencias(conn, limite: int = 20):
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM vw_transferencias_risco LIMIT %s",
            (limite,),
        )
        return cursor.fetchall()


def listar_clientes(conn):
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, nome, cidade_base FROM clientes ORDER BY id")
        return cursor.fetchall()


def resumo_por_status(conn):
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT status, COUNT(*) AS total, AVG(score_risco) AS score_medio "
            "FROM transferencias GROUP BY status"
        )
        return cursor.fetchall()
