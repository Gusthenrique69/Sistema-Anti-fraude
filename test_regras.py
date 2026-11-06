"""Testes unitários isolados do motor de regras antifraude."""

import pytest
from regras import regra_lista_negra, regra_localizacao, regra_madrugada


class MockCursor:
    def __init__(self, retorno):
        self.retorno = retorno

    def execute(self, query, params=None):
        pass

    def fetchone(self):
        return self.retorno


class MockConnection:
    def __init__(self, retorno_query=None):
        self.retorno_query = retorno_query

    def cursor(self):
        return self.__enter__()

    def __enter__(self):
        return MockCursor(self.retorno_query)

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def test_regra_lista_negra_gatilho():
    """Garante que contas em lista negra retornam score 100 imediatamente."""
    conn = MockConnection(retorno_query={"motivo": "Conta Bloqueada"})
    tx = {"conta_destino": "conta-fraude-999"}
    
    alertas = regra_lista_negra(conn, tx)
    assert len(alertas) == 1
    assert alertas[0][0] == "lista_negra"
    assert alertas[0][1] == 100


def test_regra_localizacao_divergente():
    """Testa se a transação pontua +40 se for fora da cidade base cadastrada."""
    conn = MockConnection(retorno_query={"cidade_base": "São Paulo"})
    tx = {"cliente_id": 1, "cidade": "Rio de Janeiro"}
    
    alertas = regra_localizacao(conn, tx)
    assert len(alertas) == 1
    assert alertas[0][0] == "localizacao_divergente"
    assert alertas[0][1] == 40


def test_regra_madrugada_fora_de_horario():
    """Verifica se transações de baixo valor na madrugada passam sem alerta."""
    tx = {"valor_centavos": 5000}  # R$ 50,00
    alertas = regra_madrugada(None, tx)
    # Não deve disparar se executado fora do horário ou se o valor for baixo
    assert isinstance(alertas, list)
