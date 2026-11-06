import os
import pathlib
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import pymysql

from db import conectar, criar_estrutura
from motor import processar_transferencia, listar_transferencias, listar_clientes

app = FastAPI(title="GH Bank - Painel Administrativo")

PASTA_ATUAL = pathlib.Path(__file__).parent
PASTA_TEMPLATES = PASTA_ATUAL / "templates"

criar_estrutura()

class UserLogin(BaseModel):
    email: str
    senha: str

class TransferenciaInput(BaseModel):
    cliente_id: int
    valor_centavos: int
    cidade: str
    dispositivo_id: str
    conta_destino: str

@app.get("/", response_class=HTMLResponse)
def ler_index():
    html_path = PASTA_TEMPLATES / "index.html"
    return html_path.read_text(encoding="utf-8")

# Endpoint simples para simular o Login/Cadastro no banco
@app.post("/api/auth/login")
def api_login(user: UserLogin):
    conn = conectar()
    try:
        with conn.cursor() as cursor:
            # Verifica se o usuário existe
            cursor.execute("SELECT id, nome FROM clientes WHERE email = %s", (user.email,))
            cliente = cursor.fetchone()
            if not cliente:
                # Se não existir, simula um cadastro em tempo real para fins de teste no banco
                cursor.execute(
                    "INSERT INTO clientes (nome, email, senha_hash, cidade_base) VALUES (%s, %s, %s, %s)",
                    (user.email.split('@')[0].capitalize(), user.email, user.senha, "São Paulo")
                )
                conn.commit()
                cursor.execute("SELECT id, nome FROM clientes WHERE email = %s", (user.email,))
                cliente = cursor.fetchone()
            
            return {"sucesso": True, "cliente_id": cliente["id"], "nome": cliente["nome"]}
    finally:
        conn.close()

@app.get("/api/clientes")
def api_listar_clientes():
    conn = conectar()
    try:
        return listar_clientes(conn)
    finally:
        conn.close()

@app.get("/api/transferencias")
def api_listar_transferencias():
    conn = conectar()
    try:
        return listar_transferencias(conn, limite=15)
    finally:
        conn.close()

@app.post("/api/transferencias", status_code=201)
def api_processar_transferencia(tx: TransferenciaInput):
    conn = conectar()
    try:
        dados_transferencia = {
            "cliente_id": tx.cliente_id,
            "valor_centavos": tx.valor_centavos,
            "cidade": tx.cidade,
            "dispositivo_id": tx.dispositivo_id,
            "conta_destino": tx.conta_destino
        }
        return processar_transferencia(conn, dados_transferencia)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()
