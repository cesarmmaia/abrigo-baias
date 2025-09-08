// Configurações
const ITENS_POR_PAGINA = 10;
let dadosRelatorio = [];
let estatisticasRelatorio = {};
let paginaAtual = 1;
let filtrosAtivos = {};

document.addEventListener('DOMContentLoaded', function() {
    carregarRelatorio();
    inicializarGraficos();
});

async function carregarRelatorio() {
    try {
        const response = await fetch('/api/relatorio');
        const data = await response.json();
        
        // Verificar se a API retornou a nova estrutura com estatísticas
        if (data.estatisticas && data.desinfeccoes) {
            dadosRelatorio = data.desinfeccoes;
            estatisticasRelatorio = data.estatisticas;
        } else {
            // Fallback para estrutura antiga
            dadosRelatorio = data;
            estatisticasRelatorio = {
                total: data.length,
                ok: data.filter(d => d.status === 'ok').length,
                proximo: data.filter(d => d.status === 'proximo').length,
                pendente: data.filter(d => d.status === 'pendente').length
            };
        }
        
        atualizarDashboard();
        aplicarPaginacao();
    } catch (error) {
        console.error('Erro ao carregar relatório:', error);
        alert('Erro ao carregar relatório. Verifique o console para detalhes.');
    }
}

function atualizarDashboard() {
    const dadosFiltrados = aplicarFiltrosNosDados(dadosRelatorio);
    
    // Atualizar contadores do dashboard - usar estatísticas ou calcular
    document.getElementById('countOk').textContent = estatisticasRelatorio.ok || dadosFiltrados.filter(d => d.status === 'ok').length;
    document.getElementById('countProximo').textContent = estatisticasRelatorio.proximo || dadosFiltrados.filter(d => d.status === 'proximo').length;
    document.getElementById('countPendente').textContent = estatisticasRelatorio.pendente || dadosFiltrados.filter(d => d.status === 'pendente').length;
    
    atualizarTabela(dadosFiltrados);
    atualizarGraficos(dadosFiltrados);
}

function aplicarFiltros() {
    filtrosAtivos = {
        status: document.getElementById('filterStatus').value,
        baia: document.getElementById('filterBaia').value,
        metodo: document.getElementById('filterMetodo').value,
        data: document.getElementById('filterData').value
    };
    
    paginaAtual = 1;
    atualizarDashboard();
}

function limparFiltros() {
    document.getElementById('filterStatus').value = 'todos';
    document.getElementById('filterBaia').value = '';
    document.getElementById('filterMetodo').value = 'todos';
    document.getElementById('filterData').value = '';
    
    filtrosAtivos = {};
    paginaAtual = 1;
    atualizarDashboard();
}

function aplicarFiltrosNosDados(dados) {
    return dados.filter(item => {
        // Filtro por status
        if (filtrosAtivos.status && filtrosAtivos.status !== 'todos' && item.status !== filtrosAtivos.status) {
            return false;
        }
        
        // Filtro por número da baia
        if (filtrosAtivos.baia && item.numero_baia != filtrosAtivos.baia) {
            return false;
        }
        
        // Filtro por método
        if (filtrosAtivos.metodo && filtrosAtivos.metodo !== 'todos' && item.metodo !== filtrosAtivos.metodo) {
            return false;
        }
        
        // Filtro por data
        if (filtrosAtivos.data) {
            const itemData = new Date(item.data_desinfeccao).toISOString().split('T')[0];
            const filtroData = new Date(filtrosAtivos.data).toISOString().split('T')[0];
            if (itemData !== filtroData) {
                return false;
            }
        }
        
        return true;
    });
}

function atualizarTabela(dados) {
    const tbody = document.getElementById('corpoTabelaRelatorio');
    tbody.innerHTML = '';
    
    const inicio = (paginaAtual - 1) * ITENS_POR_PAGINA;
    const fim = inicio + ITENS_POR_PAGINA;
    const dadosPagina = dados.slice(inicio, fim);
    
    dadosPagina.forEach(item => {
        const tr = document.createElement('tr');
        
        // Usar data_formatada se disponível, caso contrário formatar
        const dataFormatada = item.data_formatada || new Date(item.data_desinfeccao).toLocaleDateString('pt-BR');
        
        tr.innerHTML = `
            <td>${item.id}</td>
            <td>${item.numero_baia}</td>
            <td>${dataFormatada}</td>
            <td>${item.dias_desde_desinfeccao !== undefined ? item.dias_desde_desinfeccao : 'N/A'}</td>
            <td>${formatarMetodo(item.metodo)}</td>
            <td>${item.observacao || '-'}</td>
            <td><span class="status-badge status-${item.status}">${formatarStatus(item.status)}</span></td>
            <td>${formatarDataHora(item.atualizado_em || item.criado_em)}</td>
        `;
        
        tr.style.cursor = 'pointer';
        tr.onclick = () => mostrarDetalhes(item);
        tbody.appendChild(tr);
    });
    
    // Atualizar informações de paginação
    document.getElementById('infoPaginacao').textContent = 
        `Mostrando ${Math.min(dadosPagina.length, ITENS_POR_PAGINA)} de ${dados.length} registros`;
    
    atualizarControlesPaginacao(dados.length);
}

function formatarDataHora(dataHora) {
    if (!dataHora) return 'N/A';
    
    try {
        const data = new Date(dataHora);
        return data.toLocaleString('pt-BR');
    } catch (e) {
        return dataHora;
    }
}

function aplicarPaginacao() {
    const dadosFiltrados = aplicarFiltrosNosDados(dadosRelatorio);
    atualizarTabela(dadosFiltrados);
}

function atualizarControlesPaginacao(totalItens) {
    const totalPaginas = Math.ceil(totalItens / ITENS_POR_PAGINA);
    const paginacao = document.getElementById('paginacao');
    paginacao.innerHTML = '';
    
    if (totalPaginas <= 1) return;
    
    // Botão Anterior
    const liAnterior = document.createElement('li');
    liAnterior.className = `page-item ${paginaAtual === 1 ? 'disabled' : ''}`;
    liAnterior.innerHTML = `<a class="page-link" href="#" onclick="mudarPagina(${paginaAtual - 1}); return false;">Anterior</a>`;
    paginacao.appendChild(liAnterior);
    
    // Páginas - mostrar no máximo 5 páginas com ellipsis
    const paginaInicial = Math.max(1, paginaAtual - 2);
    const paginaFinal = Math.min(totalPaginas, paginaInicial + 4);
    
    for (let i = paginaInicial; i <= paginaFinal; i++) {
        const li = document.createElement('li');
        li.className = `page-item ${i === paginaAtual ? 'active' : ''}`;
        li.innerHTML = `<a class="page-link" href="#" onclick="mudarPagina(${i}); return false;">${i}</a>`;
        paginacao.appendChild(li);
    }
    
    // Botão Próximo
    const liProximo = document.createElement('li');
    liProximo.className = `page-item ${paginaAtual === totalPaginas ? 'disabled' : ''}`;
    liProximo.innerHTML = `<a class="page-link" href="#" onclick="mudarPagina(${paginaAtual + 1}); return false;">Próximo</a>`;
    paginacao.appendChild(liProximo);
}

function mudarPagina(pagina) {
    paginaAtual = pagina;
    const dadosFiltrados = aplicarFiltrosNosDados(dadosRelatorio);
    atualizarTabela(dadosFiltrados);
    
    // Scroll para o topo da tabela
    document.getElementById('tabelaRelatorio').scrollIntoView({ behavior: 'smooth' });
}

function formatarStatus(status) {
    const statusMap = {
        'ok': 'No Prazo',
        'proximo': 'Próximo do Prazo',
        'pendente': 'Pendente',
        'erro': 'Com Erro'
    };
    return statusMap[status] || status;
}

function formatarMetodo(metodo) {
    const metodoMap = {
        'hipoclorito': 'Hipoclorito',
        'ozonio': 'Ozônio',
        'vapor': 'Vapor'
    };
    return metodoMap[metodo] || metodo;
}

function mostrarDetalhes(item) {
    const modal = new bootstrap.Modal(document.getElementById('modalDetalhes'));
    const conteudo = document.getElementById('detalhesConteudo');
    
    const dataFormatada = item.data_formatada || new Date(item.data_desinfeccao).toLocaleDateString('pt-BR');
    
    conteudo.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <p><strong>ID:</strong> ${item.id}</p>
                <p><strong>Baia:</strong> ${item.numero_baia}</p>
                <p><strong>Data da Desinfecção:</strong> ${dataFormatada}</p>
                <p><strong>Dias desde a desinfecção:</strong> ${item.dias_desde_desinfeccao !== undefined ? item.dias_desde_desinfeccao : 'N/A'}</p>
            </div>
            <div class="col-md-6">
                <p><strong>Método:</strong> ${formatarMetodo(item.metodo)}</p>
                <p><strong>Status:</strong> <span class="status-badge status-${item.status}">${formatarStatus(item.status)}</span></p>
                <p><strong>Criado em:</strong> ${formatarDataHora(item.criado_em)}</p>
                <p><strong>Atualizado em:</strong> ${formatarDataHora(item.atualizado_em)}</p>
            </div>
        </div>
        <div class="mt-3">
            <strong>Observações:</strong>
            <p class="border p-2 rounded">${item.observacao || 'Nenhuma observação registrada.'}</p>
        </div>
    `;
    
    modal.show();
}

function exportarCSV() {
    const dadosFiltrados = aplicarFiltrosNosDados(dadosRelatorio);
    let csv = 'ID,Baia,Data Desinfecção,Data Formatada,Dias Desde,Método,Observação,Status,Última Atualização\n';
    
    dadosFiltrados.forEach(item => {
        const dataFormatada = item.data_formatada || new Date(item.data_desinfeccao).toLocaleDateString('pt-BR');
        const dataHora = formatarDataHora(item.atualizado_em || item.criado_em);
        
        csv += `"${item.id}","${item.numero_baia}","${item.data_desinfeccao}","${dataFormatada}","${item.dias_desde_desinfeccao || ''}","${item.metodo}","${item.observacao || ''}","${formatarStatus(item.status)}","${dataHora}"\n`;
    });
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `relatorio_desinfeccao_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function imprimirRelatorio() {
    window.print();
}

function inicializarGraficos() {
    // Os gráficos serão inicializados quando os dados estiverem disponíveis
}

function atualizarGraficos(dados) {
    atualizarGraficoMetodos(dados);
    atualizarGraficoStatus(dados);
}

function atualizarGraficoMetodos(dados) {
    const ctx = document.getElementById('graficoMetodos');
    if (!ctx) return;
    
    // Destruir gráfico anterior se existir
    if (ctx.chart) {
        ctx.chart.destroy();
    }
    
    const contagemMetodos = {};
    
    dados.forEach(item => {
        if (item.metodo) {
            contagemMetodos[item.metodo] = (contagemMetodos[item.metodo] || 0) + 1;
        }
    });
    
    ctx.chart = new Chart(ctx.getContext('2d'), {
        type: 'pie',
        data: {
            labels: Object.keys(contagemMetodos).map(formatarMetodo),
            datasets: [{
                data: Object.values(contagemMetodos),
                backgroundColor: ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                title: {
                    display: true,
                    text: 'Distribuição por Método de Desinfecção'
                }
            }
        }
    });
}

function atualizarGraficoStatus(dados) {
    const ctx = document.getElementById('graficoStatus');
    if (!ctx) return;
    
    // Destruir gráfico anterior se existir
    if (ctx.chart) {
        ctx.chart.destroy();
    }
    
    const contagemStatus = {
        'ok': 0,
        'proximo': 0,
        'pendente': 0,
        'erro': 0
    };
    
    dados.forEach(item => {
        if (contagemStatus.hasOwnProperty(item.status)) {
            contagemStatus[item.status]++;
        }
    });
    
    ctx.chart = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: ['No Prazo', 'Próximo do Prazo', 'Pendente', 'Com Erro'],
            datasets: [{
                label: 'Quantidade de Baias',
                data: [contagemStatus.ok, contagemStatus.proximo, contagemStatus.pendente, contagemStatus.erro],
                backgroundColor: ['#28a745', '#ffc107', '#dc3545', '#6c757d']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Status das Baias por Prazo de Desinfecção'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Quantidade de Baias'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Status'
                    }
                }
            }
        }
    });
}

// Função para recarregar os dados periodicamente (opcional)
function iniciarAtualizacaoAutomatica() {
    setInterval(() => {
        carregarRelatorio();
    }, 300000); // Recarrega a cada 5 minutos
}

// Iniciar atualização automática se necessário
// iniciarAtualizacaoAutomatica();