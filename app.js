/**
 * GH Bank - Integração do Portal de Segurança com o Motor Antifraude
 * Endpoint base da API FastAPI: http://localhost:8000
 */

const API_BASE_URL = 'http://localhost:8000';
let tokenOperador = null; // Armazena o estado de autenticação do operador

// ==========================================
// 1. FLUXO DE AUTENTICAÇÃO (LOGIN)
// ==========================================
// Substitua o trecho inicial da função realizarLogin por este:
async function realizarLogin(email, senha) {
    try {
        const resposta = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, senha })
        });

        // CORREÇÃO AQUI: mudado de reply.json() para resposta.json()
        const dados = await resposta.json(); 

        if (!resposta.ok) {
            throw new Error(dados.detail || 'Falha na autenticação.');
        }
// ... restante da função continua igual ...


// ==========================================
// 2. SUBMISSÃO DE TRANSFERÊNCIA AO MOTOR
// ==========================================
async function submeterTransferencia(evento) {
    evento.preventDefault(); // Impede o recarregamento padrão da página HTML

    const dadosFormulario = {
        cliente_id: parseInt(document.getElementById('cliente_id').value),
        valor_reais: parseFloat(document.getElementById('valor_reais').value),
        cidade: document.getElementById('cidade').value,
        dispositivo_id: document.getElementById('dispositivo_id').value,
        conta_destino: document.getElementById('conta_destino').value
    };

    try {
        const resposta = await fetch(`${API_BASE_URL}/transferencias/analisar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(dadosFormulario)
        });

        const resultado = await resposta.json();

        if (!resposta.ok) {
            throw new Error(resultado.detail || 'Erro ao processar transferência.');
        }

        // Atualiza os componentes visuais de Análise Instantânea na tela
        atualizarPainelRiscoInstantaneo(resultado);
        
        // Sincroniza a tabela histórica para exibir a nova linha inserida
        sincronizarLogs();
        
    } catch (erro) {
        exibirMensagemErro(erro.message);
    }
}

// ==========================================
// 3. SINCRONIZAÇÃO DO LIVRO DE REGISTRO
// ==========================================
async function sincronizarLogs() {
    try {
        const resposta = await fetch(`${API_BASE_URL}/transferencias/logs?limite=20`);
        const listaTransacoes = await resposta.json();

        if (!resposta.ok) throw new Error('Não foi possível obter os registros.');

        const corpoTabela = document.getElementById('tabela-registros-corpo');
        corpoTabela.innerHTML = ''; // Limpa as linhas antigas

        listaTransacoes.forEach(tx => {
            const linha = document.createElement('tr');
            
            // Define uma classe de cor CSS baseada no status de risco
            const classeStatus = {
                'aprovada': 'status-sucesso',
                'revisao_manual': 'status-alerta',
                'bloqueada': 'status-perigo'
            }[tx.status] || '';

            linha.className = classeStatus;
            linha.innerHTML = `
                <td>#${tx.id}</td>
                <td>${tx.cliente}</td>
                <td>R$ ${tx.valor_reais.toFixed(2)}</td>
                <td>${tx.cidade} (${tx.dispositivo_id})</td>
                <td>${tx.score_risco}/100</td>
                <td><span class="badge">${tx.status.toUpperCase()}</span></td>
            `;
            corpoTabela.appendChild(linha);
        });

    } catch (erro) {
        console.error('Falha na sincronização periódica:', erro);
    }
}

// ==========================================
// 4. AUXILIARES DE RENDERIZAÇÃO DE INTERFACE
// ==========================================
function atualizarPainelRiscoInstantaneo(resultado) {
    const scoreElemento = document.getElementById('score-interno');
    const regrasLista = document.getElementById('regras-violadas-lista');

    // Atualiza o medidor numérico
    scoreElemento.innerText = `${resultado.score}/100 -> ${resultado.status.toUpperCase()}`;

    // Limpa e reconstrói a listagem de regras disparadas
    regrasLista.innerHTML = '';
    if (resultado.alertas.length === 0) {
        regrasLista.innerHTML = '<li>Nenhuma regra disparada. Transação limpa.</li>';
    } else {
        resultado.alertas.forEach(([regra, pontos, detalhe]) => {
            const item = document.createElement('li');
            item.innerHTML = `<strong>${regra} (+${pontos} pts):</strong> ${detalhe}`;
            regrasLista.appendChild(item);
        });
    }
}

// Ouvintes de eventos nos formulários HTML após o carregamento da página
document.addEventListener('DOMContentLoaded', () => {
    // Intercepta o formulário de Transferência
    const formTx = document.getElementById('form-solicitar-transferencia');
    if (formTx) formTx.addEventListener('submit', submeterTransferencia);

    // Botão manual de Sincronizar Logs
    const btnSincronizar = document.getElementById('btn-sincronizar');
    if (btnSincronizar) btnSincronizar.addEventListener('click', sincronizarLogs);
});
// ==========================================
// ALTERNAR ENTRE TELA DE LOGIN E CADASTRO
// ==========================================
function alternarTelasAuth(exibirCadastro) {
    const cardLogin = document.getElementById('card-login');
    const cardCadastro = document.getElementById('card-cadastro');
    
    // Limpa mensagens de erro antigas
    document.getElementById('mensagem-login-erro').innerText = '';
    document.getElementById('mensagem-cadastro-erro').innerText = '';

    if (exibirCadastro) {
        cardLogin.style.display = 'none';
        cardCadastro.style.display = 'block';
    } else {
        cardLogin.style.display = 'block';
        cardCadastro.style.display = 'none';
    }
}

// ==========================================
// REQUISIÇÃO DE CRIAÇÃO DE CONTA (REGISTRO)
// ==========================================
async function criarConta(evento) {
    evento.preventDefault();

    const dadosCadastro = {
        nome: document.getElementById('nome-cadastro').value,
        email: document.getElementById('email-cadastro').value,
        cidade_base: document.getElementById('cidade-cadastro').value,
        senha: document.getElementById('senha-cadastro').value
    };

    const msgErroDiv = document.getElementById('mensagem-cadastro-erro');
    msgErroDiv.innerText = ''; // Limpa mensagens anteriores

    try {
        const resposta = await fetch(`${API_BASE_URL}/auth/registrar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(dadosCadastro)
        });

        const dados = await resposta.json();

        if (!resposta.ok) {
            throw new Error(dados.detail || 'Não foi possível realizar o cadastro.');
        }

        // Cadastro feito com sucesso: avisa o usuário e joga ele para a tela de login
        alert('Conta criada com sucesso! Faça login para acessar o sistema.');
        document.getElementById('form-cadastro').reset();
        alternarTelasAuth(false); // Retorna para a tela de login

    } catch (erro) {
        msgErroDiv.innerText = erro.message;
    }
}

// Adicione o ouvinte do formulário de cadastro dentro do seu DOMContentLoaded já existente:
document.addEventListener('DOMContentLoaded', () => {
    // ... manter ouvintes anteriores ...
    
    const formCadastro = document.getElementById('form-cadastro');
    if (formCadastro) formCadastro.addEventListener('submit', criarConta);
});
