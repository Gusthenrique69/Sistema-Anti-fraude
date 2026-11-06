"""API Web do GH Bank conectando a interface ao motor antifraude."""

import bcrypt
from db import conectar, criar_estrutura
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from motor import listar_transferencias, processar_transferencia
from pydantic import BaseModel, Field

app = FastAPI(title="GH Bank - API Antifraude em Tempo Real")

# Libera chamadas do front-end da interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializa o banco de dados ao iniciar a API
conn_global = criar_estrutura()


class LoginSchema(BaseModel):
    email: str
    senha: str


class RegistroSchema(BaseModel):
    nome: str
    email: str
    senha: str
    cidade_base: str


class TransferenciaSchema(BaseModel):
    cliente_id: int
    valor_reais: float = Field(..., gt=0)
    cidade: str
    dispositivo_id: str
    conta_destino: str


@app.post("/auth/login")
def login(dados: LoginSchema):
    """Autentica o operador do portal comparando o hash criptografado."""
    with conn_global.cursor() as cursor:
        cursor.execute("SELECT id, nome, senha_hash FROM clientes WHERE email = %s", (dados.email,))
        usuario = cursor.fetchone()

    if not usuario or not bcrypt.checkpw(dados.senha.encode('utf-8'), usuario['senha_hash'].encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail corporativo ou senha incorretos."
        )

    return {"status": "sucesso", "operador": usuario["nome"]}


@app.post("/auth/registrar", status_code=status.HTTP_201_CREATED)
def registrar_cliente(dados: RegistroSchema):
    """Cria um novo cliente no sistema gerando um hash seguro para a senha."""
    salt = bcrypt.gensalt(rounds=12)
    senha_hash = bcrypt.hashpw(dados.senha.encode('utf-8'), salt).decode('utf-8')
    
    try:
        with conn_global.cursor() as cursor:
            cursor.execute("SELECT id FROM clientes WHERE email = %s", (dados.email,))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Este e-mail corporativo já está cadastrado."
                )
                
            sql = """
                INSERT INTO clientes (nome, email, senha_hash, score_credito, cidade_base)
                VALUES (%s, %s, %s, 500, %s)
            """
            cursor.execute(sql, (dados.nome.strip(), dados.email.strip(), senha_hash, dados.cidade_base.strip()))
            conn_global.commit()
            
        return {"status": "sucesso", "mensagem": "Conta criada com sucesso!"}
        
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        conn_global.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao salvar no banco: {str(e)}")


@app.post("/transferencias/analisar")
def analisar_via_api(tx_web: TransferenciaSchema):
    """Recebe transações da interface web e submete ao motor de risco."""
    tx_formatada = {
        "cliente_id": tx_web.cliente_id,
        "valor_centavos": int(round(tx_web.valor_reais * 100)),
        "cidade": tx_web.cidade.strip(),
        "dispositivo_id": tx_web.dispositivo_id.strip(),
        "conta_destino": tx_web.conta_destino.strip(),
    }

    try:
        resultado = processar_transferencia(conn_global, tx_formatada)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no motor: {str(e)}")


@app.get("/transferencias/logs")
def obter_logs(limite: int = 20):
    """Retorna o Livro de Registro de Transferências atualizado."""
    return listar_transferencias(conn_global, limite)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
