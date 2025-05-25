// Configuração do tema
document.addEventListener('DOMContentLoaded', () => {
    const btnMudarTema = document.getElementById('btn-mudar-tema');
    btnMudarTema.addEventListener('click', () => {
        const html = document.documentElement;
        const temaAtual = html.getAttribute('data-bs-theme');
        html.setAttribute('data-bs-theme', temaAtual === 'dark' ? 'light' : 'dark');
    });
});

// Gerenciamento de linhas do grid
let contadorLinhas = 1;

document.getElementById('btn-adicionar-linha').addEventListener('click', () => {
    contadorLinhas++;
    adicionarLinha(contadorLinhas);
    atualizarBotoesRemover();
});

function adicionarLinha(numero) {
    const template = `
        <div class="row grid-row" id="row-${numero}">
            <div class="col-md-6 mb-3">
                <label for="termos-${numero}" class="form-label">Termos</label>
                <textarea style="max-height: 86px;" class="form-control" id="termos-${numero}" rows="3" maxlength="128" placeholder="Ex: Grand Theft Auto V"></textarea>
            </div>
            <div class="col-md-4 mb-3">
                <label for="loja-${numero}" class="form-label">Plataforma</label>
                <select class="form-select" id="loja-${numero}">
                    <option value="" selected disabled>Selecionar...</option>
                    <option value="steam">Steam</option>
                </select>
            </div>
            <div class="col-md-2 mb-3 d-flex align-items-end">
                <div class="btn-actions">
                    <button type="button" class="btn btn-danger btn-remover" data-row="${numero}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16">
                            <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z"/>
                            <path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4zM2.5 3h11V2h-11z"/>
                        </svg>
                        Remover
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('grid-container').insertAdjacentHTML('beforeend', template);
    
    // Adiciona evento de remoção
    document.querySelector(`#row-${numero} .btn-remover`).addEventListener('click', (e) => {
        const rowId = e.currentTarget.getAttribute('data-row');
        document.getElementById(`row-${rowId}`).remove();
        atualizarBotoesRemover();
    });
}

function atualizarBotoesRemover() {
    const linhas = document.querySelectorAll('.grid-row');
    const botoes = document.querySelectorAll('.btn-remover');
    
    botoes.forEach(botao => {
        botao.disabled = linhas.length <= 1;
    });
}

// Websocket e busca de produtos
let ws = null;
let totalProdutosEncontrados = 0;

document.getElementById('btn-pesquisar').addEventListener('click', iniciarBusca);

function iniciarBusca() {
    const linhas = document.querySelectorAll('.grid-row');
    const buscas = [];
    
    for (const linha of linhas) {
        const numero = linha.id.split('-')[1];
        const termos = document.getElementById(`termos-${numero}`).value.trim();
        const loja = document.getElementById(`loja-${numero}`).value;
        
        if (!termos || !loja) {
            alert('Por favor, preencha todos os campos antes de pesquisar.');
            return;
        }
        
        buscas.push({ termos, loja });
    }
    
    // Reseta contadores e mostra seção de resultados
    totalProdutosEncontrados = 0;
    document.getElementById('contador-produtos').textContent = '0';
    document.getElementById('progresso-texto').textContent = '0% concluído';
    document.getElementById('barra-progresso').style.width = '0%';
    document.getElementById('barra-progresso').textContent = '0%';
    
    // Inicializa o container de resultados
    const container = document.getElementById('resultados-container');
    container.innerHTML = '<div class="row row-cols-1 row-cols-md-3 g-4"></div>';
    
    document.getElementById('secao-resultados').style.display = 'block';
    document.getElementById('loading-spinner').style.display = 'block';
    
    // Conecta ao WebSocket
    if (ws) {
        ws.close();
    }
    
    ws = new WebSocket('ws://localhost:8765');
    
    ws.onopen = () => {
        console.log('Conectado ao servidor WebSocket');
        ws.send(JSON.stringify(buscas));
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        // Atualiza a barra de progresso
        if (data.tipo === 'resultado_parcial') {
            const porcentagem = Math.min(100, data.progresso);
            document.getElementById('progresso-texto').textContent = `${Math.round(porcentagem)}% concluído`;
            document.getElementById('barra-progresso').style.width = `${porcentagem}%`;
            document.getElementById('barra-progresso').textContent = `${Math.round(porcentagem)}%`;
            
            // Atualiza o contador de produtos
            if (data.produtos && data.produtos.length > 0) {
                const contadorAtual = parseInt(document.getElementById('contador-produtos').textContent) || 0;
                document.getElementById('contador-produtos').textContent = contadorAtual + data.produtos.length;
                mostrarResultados(data.produtos, true);
            }
        } else if (data.tipo === 'busca_concluida') {
            document.getElementById('loading-spinner').style.display = 'none';
            
            const totalProdutos = parseInt(document.getElementById('contador-produtos').textContent) || 0;
            if (totalProdutos === 0) {
                document.getElementById('resultados-container').innerHTML = 
                    '<div class="alert alert-warning">Nenhum jogo encontrado.</div>';
            }
        }
    };
    
    ws.onerror = (error) => {
        console.error('Erro no WebSocket:', error);
        alert('Erro ao conectar com o servidor. Verifique se o servidor está rodando.');
    };
    
    ws.onclose = () => {
        console.log('Conexão WebSocket fechada');
        document.getElementById('loading-spinner').style.display = 'none';
    };
}

function mostrarResultados(produtos, append = false) {
    if (!produtos || produtos.length === 0) return;
    
    const container = document.getElementById('resultados-container');
    const cardContainer = container.querySelector('.row');
    
    if (!cardContainer) {
        console.error('Container de cards não encontrado');
        return;
    }
    
    for (const jogo of produtos) {
        const card = `
            <div class="col">
                <div class="card h-100">
                    <img src="${jogo.imagem}" class="card-img-top" alt="${jogo.nome}" onerror="this.src='https://via.placeholder.com/300x300?text=Imagem+não+disponível'">
                    <div class="card-body">
                        <h5 class="card-title">${jogo.nome}</h5>
                        <p class="card-text">
                            <strong>Plataforma:</strong> ${jogo.plataforma}<br>
                            <strong>Lançamento:</strong> ${jogo.lancamento}<br>
                            <strong>Distribuidora:</strong> ${jogo.distribuidora}<br>
                            <strong>Preço:</strong> ${jogo.preco}
                        </p>
                        <a href="${jogo.link}" class="btn btn-primary" target="_blank">Ver na Loja</a>
                    </div>
                </div>
            </div>
        `;
        cardContainer.insertAdjacentHTML('beforeend', card);
    }
}