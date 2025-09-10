document.addEventListener('DOMContentLoaded', function() {
    carregarBaias();            // Preenche o drop-down com as baias
    carregarAgendamentos();     // Carrega os agendamentos pendentes
    document.getElementById('formAgendamento')
        .addEventListener('submit', criarAgendamento);
});

/**
 * Carrega as baias no menu drop-down.
 * Aqui usamos 10 baias fixas, mas pode ser adaptado para vir do backend.
 */
async function carregarBaias() {
    try {
        const totalBaias = 10; // número de baias fixo
        const select = document.getElementById('agendamentoBaia');

        // Limpa opções antigas
        select.innerHTML = '<option value="">Selecione a baia</option>';

        for (let i = 1; i <= totalBaias; i++) {
            const option = document.createElement('option');
            option.value = i;
            option.textContent = `Baia ${i}`;
            select.appendChild(option);
        }
    } catch (error) {
        console.error("Erro ao carregar baias:", error);
    }
}

/**
 * Busca agendamentos pendentes no backend.
 */
async function carregarAgendamentos() {
    try {
        const response = await fetch('/api/agendamentos');
        const agendamentos = await response.json();
        exibirAgendamentos(agendamentos);
    } catch (error) {
        console.error('Erro ao carregar agendamentos:', error);
    }
}

/**
 * Exibe os agendamentos na tabela.
 */
function exibirAgendamentos(agendamentos) {
    const tbody = document.getElementById('listaAgendamentos');
    tbody.innerHTML = '';

    if (!agendamentos || agendamentos.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center">Nenhum agendamento encontrado</td></tr>`;
        return;
    }

    agendamentos.forEach(agendamento => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${agendamento.numero_baia}</td>
            <td>${agendamento.data_agendamento}</td>
            <td>${formatarMetodo(agendamento.metodo)}</td>
            <td>${agendamento.status_agendamento}</td>
            <td>
                <button class="btn btn-sm btn-success" onclick="realizarAgendamento(${agendamento.id})">Realizar</button>
                <button class="btn btn-sm btn-danger" onclick="cancelarAgendamento(${agendamento.id})">Cancelar</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

/**
 * Cria um novo agendamento.
 */
async function criarAgendamento(event) {
    event.preventDefault();

    const data = {
        numero_baia: document.getElementById('agendamentoBaia').value,
        data_agendamento: document.getElementById('agendamentoData').value,
        metodo: document.getElementById('agendamentoMetodo').value,
        observacao: document.getElementById('agendamentoObservacao').value
    };

    try {
        const response = await fetch('/api/agendamentos', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });

        if (response.ok) {
            alert('Agendamento criado com sucesso!');
            event.target.reset();
            carregarAgendamentos();
        } else {
            const err = await response.json();
            alert(err.error || 'Erro ao criar agendamento.');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Falha ao criar agendamento.');
    }
}

/**
 * Marca um agendamento como realizado.
 */
async function realizarAgendamento(id) {
    try {
        const data = { data_realizacao: new Date().toISOString().split('T')[0] };
        const response = await fetch(`/api/agendamentos/${id}/realizar`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });

        if (response.ok) {
            alert('Agendamento realizado!');
            carregarAgendamentos();
        } else {
            const err = await response.json();
            alert(err.error || 'Erro ao realizar agendamento.');
        }
    } catch (error) {
        console.error('Erro:', error);
    }
}

/**
 * Cancela um agendamento existente.
 */
async function cancelarAgendamento(id) {
    if (!confirm('Tem certeza que deseja cancelar este agendamento?')) return;

    try {
        const response = await fetch(`/api/agendamentos/${id}`, { method: 'DELETE' });
        if (response.ok) {
            alert('Agendamento cancelado.');
            carregarAgendamentos();
        } else {
            const err = await response.json();
            alert(err.error || 'Erro ao cancelar agendamento.');
        }
    } catch (error) {
        console.error('Erro:', error);
    }
}

/**
 * Utilitário: formata nomes dos métodos de desinfecção.
 */
function formatarMetodo(metodo) {
    const mapa = {
        'hipoclorito': 'Hipoclorito',
        'ozonio': 'Ozônio',
        'vapor': 'Vapor'
    };
    return mapa[metodo] || metodo;
}
