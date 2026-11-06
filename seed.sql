USE antifraude;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE alertas_fraude;
TRUNCATE TABLE transferencias;
TRUNCATE TABLE clientes;
TRUNCATE TABLE lista_negra_contas;
SET FOREIGN_KEY_CHECKS = 1;

-- Clientes com e-mail e hashes seguros (senha padrão de teste para todos: "senha123")
INSERT INTO clientes (id, nome, email, senha_hash, score_credito, cidade_base) VALUES
    (1, 'Rodrigo Silva', 'rodrigo@ghbank.com.br', '$2b$12$Z0H7kM9Y1pEshlXz1mYJDeH6lby3bZ1D1jT.S7g3XQ3q4zfeP2Fw.', 850, 'São Paulo'),
    (2, 'Alessandra Helena', 'alessandra@ghbank.com.br', '$2b$12$Z0H7kM9Y1pEshlXz1mYJDeH6lby3bZ1D1jT.S7g3XQ3q4zfeP2Fw.', 720, 'Campinas'),
    (3, 'Marcos Antunes', 'marcos@ghbank.com.br', '$2b$12$Z0H7kM9Y1pEshlXz1mYJDeH6lby3bZ1D1jT.S7g3XQ3q4zfeP2Fw.', 610, 'Belo Horizonte');

INSERT INTO lista_negra_contas (conta_destino, motivo) VALUES
    ('conta-fraude-999', 'Conta denunciada por golpe do Pix falso'),
    ('laranja-0042',     'Conta laranja identificada pelo time de risco');

-- Histórico de transações vinculadas dinamicamente ao momento presente
INSERT INTO transferencias (cliente_id, valor_centavos, cidade, dispositivo_id, conta_destino, score_risco, status, data_hora) VALUES
    (1, 5000, 'São Paulo', 'celular-rodrigo', 'loja-padaria',      0, 'aprovada', NOW() - INTERVAL 10 MINUTE),
    (1, 4500, 'São Paulo', 'celular-rodrigo', 'posto-combustivel', 0, 'aprovada', NOW() - INTERVAL 8 MINUTE),
    (1, 5500, 'São Paulo', 'celular-rodrigo', 'supermercado',      0, 'aprovada', NOW() - INTERVAL 6 MINUTE),
    (2, 12000,'Campinas',  'celular-ale',     'faculdade',         0, 'aprovada', NOW() - INTERVAL 2 MINUTE);
