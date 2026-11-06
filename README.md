# Antifraude — Python + MySQL
# Sistema Antifraude em Tempo Real — Score de Risco de Transação

## 1. Instalar dependência
```bash
pip install pymysql
Projeto completo com **MySQL Workbench** (banco) + **Python no VS Code** (motor de regras).

## Como funciona

Cada transferência recebe um **score de risco de 0 a 100**, somando pontos das regras:

| Regra | Pontos | O que verifica |
|---|---|---|
| Lista negra | 100 (bloqueio imediato) | Conta de destino denunciada |
| Localização divergente | +40 | Cidade diferente da cidade base do cliente |
| Velocidade | +35 | 3 ou mais transferências em 5 minutos |
| Valor atípico | +25 | Valor acima de 3x a média das últimas 10 |
| Aparelho novo | +20 | Primeiro uso daquele dispositivo |
| Horário incomum | +15 | Valor alto entre 0h e 5h |

Decisão final:
- **0 a 30** → aprovada
- **31 a 70** → revisão manual
- **71 a 100** → bloqueada

## Arquivos

```
antifraude/
├── schema.sql        tabelas, índices e a view de relatório
├── seed.sql          dados de exemplo (clientes, lista negra, histórico)
├── db.py             conexão com o MySQL e criação automática do banco
├── regras.py         as regras antifraude e os limites de score
├── motor.py          grava a transferência + os alertas no banco
├── simulacao.py      roda 3 cenários prontos (normal, suspeito, fraude)
├── app.py            menu interativo para analisar transferências
├── requirements.txt  dependências
└── .env.example      modelo de configuração do banco
```

## 2. Criar o banco e as tabelas
Abra o MySQL Workbench e execute todo o arquivo `antifraude/schema.sql`
(ícone do raio ⚡). O próprio arquivo já cria o banco `antifraude` e faz
`USE antifraude;` — então você não precisa rodar o `USE` antes.
## Passo a passo

Ou pelo terminal:
### 1. Criar o banco no MySQL Workbench
Abra `schema.sql`, execute tudo (⚡). Depois abra `seed.sql` e execute também.
O `schema.sql` já cria o banco `antifraude`, então não precisa rodar `USE` antes.

Pelo terminal, se preferir:
```bash
mysql -u root -p < antifraude/schema.sql
mysql -u root -p < antifraude/seed.sql
```

## 3. Configurar a conexão do Python
Use variáveis de ambiente (valores padrão: host localhost, porta 3306,
banco `antifraude`, usuário `root`):
### 2. Preparar o Python no VS Code
```bash
export DB_HOST=localhost DB_PORT=3306 DB_NAME=antifraude DB_USER=root DB_PASSWORD=sua_senha
cd antifraude
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Rodar a simulação
### 3. Configurar a senha do banco
Copie `.env.example` para `.env` e preencha `DB_PASSWORD` (e `DB_USER`, se não for `root`).

### 4. Rodar
```bash
python antifraude/antifraude.py
python simulacao.py   # demonstração com os 3 cenários
python app.py         # menu interativo
```
Rode de dentro da pasta `antifraude` (é assim que os imports se encontram).

## Consultas úteis no Workbench

```sql
USE antifraude;

-- painel de transferências com risco
SELECT * FROM vw_transferencias_risco;

-- quais regras dispararam em cada transferência
SELECT t.id, t.status, t.score_risco, a.regra, a.pontos, a.detalhe
FROM transferencias t
LEFT JOIN alertas_fraude a ON a.transferencia_id = t.id
ORDER BY t.id DESC;

-- fila de revisão manual
SELECT * FROM vw_transferencias_risco WHERE status = 'revisao_manual';
```

## Por que os erros anteriores aconteceram
- `Unknown database 'sistema_antifraude' / 'antifraude'` (erro 1049): o
  banco ainda não existia. O novo `schema.sql` começa com
  `CREATE DATABASE IF NOT EXISTS antifraude;` e resolve isso.
- Erro 1064 no `CREATE INDEX IF NOT EXISTS`: isso é sintaxe de
  PostgreSQL, que o MySQL não aceita. No novo arquivo o índice é criado
  dentro do `CREATE TABLE`, no formato do MySQL.
- O Python também trocou de driver: `pymysql` no lugar de `psycopg`
  (que só funciona com PostgreSQL).
## Erros comuns

## Observação importante
A tabela `transferencias` do seu SQL original não tinha a coluna
`conta_destino`, mas o código Python precisa dela (regra da lista negra).
Ela foi adicionada no `schema.sql`.
- **1049 Unknown database** → rode o `schema.sql` inteiro; ele cria o banco.
- **1064 perto de `IF NOT EXISTS`** em `CREATE INDEX` → sintaxe do PostgreSQL; aqui os índices já estão dentro do `CREATE TABLE`.
- **`Access denied for user`** → senha errada no `.env`.
- **`No module named pymysql`** → falta rodar `pip install -r requirements.txt` com o ambiente virtual ativo.
