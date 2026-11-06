-- =====================================================================
-- Sistema Antifraude em Tempo Real - Banco de dados (MySQL) - CORRIGIDO
-- =====================================================================

CREATE DATABASE IF NOT EXISTS antifraude
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE antifraude;

-- 1. Tabela de Clientes (Corrigida: campos de login embutidos na criação)
CREATE TABLE IF NOT EXISTS clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    score_credito INT NOT NULL DEFAULT 500,
    cidade_base VARCHAR(100) NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabela de Contas na Lista Negra
CREATE TABLE IF NOT EXISTS lista_negra_contas (
    conta_destino VARCHAR(50) PRIMARY KEY,
    motivo VARCHAR(255),
    data_inclusao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabela de Transferências
CREATE TABLE IF NOT EXISTS transferencias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    valor_centavos INT NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    dispositivo_id VARCHAR(50) NOT NULL,
    conta_destino VARCHAR(50) NOT NULL,
    score_risco INT NOT NULL DEFAULT 0,
    status ENUM('aprovada', 'revisao_manual', 'bloqueada') NOT NULL DEFAULT 'aprovada',
    data_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_transferencias_cliente
        FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    INDEX idx_transferencias_cliente_data (cliente_id, data_hora),
    INDEX idx_transferencias_dispositivo (cliente_id, dispositivo_id)
);

-- 4. Trilha de Auditoria
CREATE TABLE IF NOT EXISTS alertas_fraude (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transferencia_id INT NOT NULL,
    regra VARCHAR(60) NOT NULL,
    pontos INT NOT NULL,
    detalhe VARCHAR(255),
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_alertas_transferencia
        FOREIGN KEY (transferencia_id) REFERENCES transferencias(id)
        ON DELETE CASCADE,
    INDEX idx_alertas_transferencia (transferencia_id)
);

-- 5. Visão para Relatório
CREATE OR REPLACE VIEW vw_transferencias_risco AS
SELECT  t.id,
        c.nome AS cliente,
        t.valor_centavos / 100 AS valor_reais,
        t.cidade,
        t.dispositivo_id,
        t.conta_destino,
        t.score_risco,
        t.status,
        t.data_hora
FROM transferencias t
JOIN clientes c ON c.id = t.cliente_id
ORDER BY t.data_hora DESC;
