let currentDate = new Date();
let currentMonth = currentDate.getMonth();
let currentYear = currentDate.getFullYear();
let selectedAgendamentoId = null;

document.addEventListener('DOMContentLoaded', function() {
    carregarBaias();
    carregarConfiguracao();
    carregarAgendamentos();
    renderCalendar();
});

function carregarBaias() {
    const select = document.getElementById('agendamentoBaia');
    for (let i = 1; i <= 20; i++) {
        const option = document.createElement('option');
        option.value = i;
        option.textContent = `Baia ${i}`;
        select.appendChild(option);
    }
    
    select.addEventListener('change', function() {
        const baia = this.value;
        if (baia) {
            carregarProximaData(baia);
        }
    });
}

async function carregarProximaData(numeroBaia) {
    try {
        const response = await fetch(`/api/proximo-agendamento/${numeroBaia}`);
        const data = await response.json();
        
        const dataInput = document.getElementById('agendamentoData');
        const infoText = document.getElementById('proximaDataInfo');
        
        if (data.proxima_data) {
            dataInput.value = data.proxima_data;
            infoText.textContent = `Próxima desinfecção recomendada: ${new Date(data.proxima_data).toLocaleDateString('pt-BR')}`;
            infoText.className = 'form-text text-success';
        } else {
            // Se não há histórico, sugere data atual + intervalo
            const intervalo = data.intervalo_dias || 15;
            const proximaData = new Date();
            proximaData.setDate(proximaData.getDate() + intervalo);
            dataInput.value = proximaData.toISOString().split('T')[0];
            infoText.textContent = `Primeira desinfecção - intervalo padrão: ${intervalo} dias`;
            infoText.className = 'form-text text-info';
        }
    } catch (error) {
        console.error('Erro ao carregar próxima data:', error);
    }
}

async function carregarConfiguracao() {
    try {
        const response = await fetch('/api/config/agendamento');
        const config = await response.json();
        
        if (config.intervalo_dias) {
            document.getElementById('intervaloDias').value = config.intervalo_dias;
        }
    } catch (error) {
        console.error('Erro ao carregar configuração:', error);
    }
}

async function salvarConfiguracao() {
    try {
        const intervalo = document.getElementById('intervaloDias').value;
        
        const response = await fetch('/api/config/agendamento', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ intervalo_dias: parseInt(intervalo) })
        });
        
        if (response.ok) {
            alert('Configuração salva com sucesso!');
        } else {
            throw new Error('Erro ao salvar configuração');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao salvar configuração.');
    }
}

async function carregarAgendamentos() {
    try {
        const response = await fetch('/api/agendamentos');
        const agendamentos = await response.json();
        atualizarListaAgendamentos(agendamentos);
    } catch (error) {
        console.error('Erro ao carregar agendamentos:', error);
    }
}

function atualizarListaAgendamentos(agendamentos) {
    const tbody = document.getElementById('listaAgendamentos');
    tbody.innerHTML = '';
    
    if (agendamentos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-muted py-3">
                    Nenhum agendamento pendente
                </td>
            </tr>
        `;
        return;
    }
    
    agendamentos.forEach(agendamento => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>Baia ${agendamento.numero_baia}</td>
            <td>${new Date(agendamento.data_agendamento).toLocaleDateString('pt-BR')}</td>
            <td>${formatarMetodo(agendamento.metodo)}</td>
            <td><span class="badge bg-warning">Pendente</span></td>
            <td>
                <button class="btn btn-sm btn-success me-1" onclick="abrirModalRealizar(${agendamento.id}, ${agendamento.numero_baia})">
                    <i class="bi bi-check-circle"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="cancelarAgendamento(${agendamento.id})">
                    <i class="bi bi-x-circle"></i>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function abrirModalRealizar(id, numeroBaia) {
    selectedAgendamentoId = id;
    document.getElementById('modalBaia').textContent = `Baia ${numeroBaia}`;
    document.getElementById('dataRealizacao').value = new Date().toISOString().split('T')[0];
    
    const modal = new bootstrap.Modal(document.getElementById('modalRealizarAgendamento'));
    modal.show();
}

async function confirmarRealizacao() {
    try {
        const dataRealizacao = document.getElementById('dataRealizacao').value;
        
        const response = await fetch(`/api/agendamentos/${selectedAgendamentoId}/realizar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ data_realizacao: dataRealizacao })
        });
        
        if (response.ok) {
            alert('Agendamento realizado com sucesso!');
            $('#modalRealizarAgendamento').modal('hide');
            carregarAgendamentos();
            renderCalendar();
        } else {
            throw new Error('Erro ao realizar agendamento');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao realizar agendamento.');
    }
}

async function cancelarAgendamento(id) {
    if (!confirm('Tem certeza que deseja cancelar este agendamento?')) return;
    
    try {
        const response = await fetch(`/api/agendamentos/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            alert('Agendamento cancelado com sucesso!');
            carregarAgendamentos();
            renderCalendar();
        } else {
            throw new Error('Erro ao cancelar agendamento');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao cancelar agendamento.');
    }
}

// Funções do calendário
function renderCalendar() {
    const calendar = document.getElementById('calendar');
    calendar.innerHTML = '';
    
    const firstDay = new Date(currentYear, currentMonth, 1);
    const lastDay = new Date(currentYear, currentMonth + 1, 0);
    const daysInMonth = lastDay.getDate();
    
    document.getElementById('currentMonth').textContent = 
        firstDay.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' });
    
    // Cabeçalho dos dias da semana
    const weekdays = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
    weekdays.forEach(day => {
        const div = document.createElement('div');
        div.className = 'col text-center fw-bold';
        div.textContent = day;
        calendar.appendChild(div);
    });
    
    // Dias vazios no início
    for (let i = 0; i < firstDay.getDay(); i++) {
        const emptyDiv = document.createElement('div');
        emptyDiv.className = 'col calendar-day';
        calendar.appendChild(emptyDiv);
    }
    
    // Dias do mês
    for (let day = 1; day <= daysInMonth; day++) {
        const dayDiv = document.createElement('div');
        dayDiv.className = 'col calendar-day';
        
        const dayNumber = document.createElement('div');
        dayNumber.className = 'day-number';
        dayNumber.textContent = day;
        dayDiv.appendChild(dayNumber);
        
        const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        
        // Verificar se é hoje
        const today = new Date();
        if (currentYear === today.getFullYear() && currentMonth === today.getMonth() && day === today.getDate()) {
            dayDiv.classList.add('today');
        }
        
        // Verificar se tem agendamentos neste dia
        if (hasAgendamento(dateStr)) {
            dayDiv.classList.add('has-agendamento');
            const agendamentos = getAgendamentosPorData(dateStr);
            
            agendamentos.forEach(ag => {
                const agDiv = document.createElement('div');
                agDiv.className = 'agendamento-item bg-warning';
                agDiv.textContent = `Baia ${ag.numero_baia}`;
                agDiv.title = `Método: ${formatarMetodo(ag.metodo)}`;
                dayDiv.appendChild(agDiv);
            });
        }
        
        calendar.appendChild(dayDiv);
    }
}

function hasAgendamento(dateStr) {
    // Implementar lógica para verificar agendamentos
    return false;
}

function getAgendamentosPorData(dateStr) {
    // Implementar lógica para obter agendamentos por data
    return [];
}

function previousMonth() {
    currentMonth--;
    if (currentMonth < 0) {
        currentMonth = 11;
        currentYear--;
    }
    renderCalendar();
}

function nextMonth() {
    currentMonth++;
    if (currentMonth > 11) {
        currentMonth = 0;
        currentYear++;
    }
    renderCalendar();
}

function formatarMetodo(metodo) {
    const metodoMap = {
        'hipoclorito': 'Hipoclorito',
        'ozonio': 'Ozônio',
        'vapor': 'Vapor'
    };
    return metodoMap[metodo] || metodo;
}

// Event listener para o formulário de agendamento
document.getElementById('formAgendamento').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = {
        numero_baia: parseInt(document.getElementById('agendamentoBaia').value),
        data_agendamento: document.getElementById('agendamentoData').value,
        metodo: document.getElementById('agendamentoMetodo').value,
        observacao: document.getElementById('agendamentoObservacao').value
    };
    
    try {
        const response = await fetch('/api/agendamentos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            alert('Agendamento criado com sucesso!');
            this.reset();
            carregarAgendamentos();
            renderCalendar();
        } else {
            throw new Error('Erro ao criar agendamento');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao criar agendamento. Verifique o console para detalhes.');
    }
});

async function salvarAgendamento(event) {
    event.preventDefault();
    
    if (!currentBaiaForAgendamento) {
        alert('Por favor, selecione uma baia primeiro.');
        return;
    }
    
    const agendamento = {
        numero_baia: currentBaiaForAgendamento,
        data_agendamento: document.getElementById('dataAgendamento').value,
        metodo: document.getElementById('metodo').value,
        observacao: document.getElementById('observacao').value
    };
    
    // Validação básica
    if (!agendamento.data_agendamento || !agendamento.metodo) {
        alert('Por favor, preencha todos os campos obrigatórios.');
        return;
    }
    
    try {
        const response = await fetch('/api/agendamentos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(agendamento)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            mostrarModalSucesso(
                'Agendamento Criado',
                `Desinfecção da Baia ${agendamento.numero_baia} agendada para ${new Date(agendamento.data_agendamento).toLocaleDateString('pt-BR')}`
            );
            ocultarFormAgendamento();
            carregarDadosIniciais();
        } else {
            throw new Error(result.error || 'Erro ao criar agendamento');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert(`Erro ao criar agendamento: ${error.message}`);
    }
}