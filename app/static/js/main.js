document.addEventListener('DOMContentLoaded', function() {
    carregarDesinfeccoes();
    document.getElementById('formDesinfeccao').addEventListener('submit', salvarDesinfeccao);
});

async function carregarDesinfeccoes() {
    try {
        const response = await fetch('/desinfeccoes');
        const desinfeccoes = await response.json();
        exibirDesinfeccoes(desinfeccoes);
    } catch (error) {
        console.error('Erro ao carregar desinfecções:', error);
    }
}

function exibirDesinfeccoes(desinfeccoes) {
    const tbody = document.getElementById('listaDesinfeccoes');
    tbody.innerHTML = '';

    desinfeccoes.forEach(desinfeccao => {
        const tr = document.createElement('tr');

        // Calcular status
        const dataDesinfeccao = new Date(desinfeccao.data_desinfeccao);
        const diasDiff = Math.floor((new Date() - dataDesinfeccao) / (1000 * 60 * 60 * 24));
        let status = 'OK';
        let statusClass = 'status-ok';

        if (diasDiff >= 15) {
            status = 'Pendente';
            statusClass = 'status-pendente';
        } else if (diasDiff >= 10) {
            status = 'Próximo';
            statusClass = 'status-proximo';
        }

        tr.innerHTML = `
            <td>${desinfeccao.numero_baia}</td>
            <td>${new Date(desinfeccao.data_desinfeccao).toLocaleDateString()}</td>
            <td>${desinfeccao.metodo}</td>
            <td>${desinfeccao.observacao || '-'}</td>
            <td><span class="status ${statusClass}">${status}</span></td>
            <td>
                <button class="btn btn-sm btn-outline-danger" onclick="deletarDesinfeccao(${desinfeccao.id})">Excluir</button>
            </td>
        `;

        tbody.appendChild(tr);
    });
}

async function salvarDesinfeccao(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const desinfeccao = {
        numero_baia: parseInt(formData.get('numero_baia')),
        data_desinfeccao: formData.get('data_desinfeccao'),
        metodo: formData.get('metodo'),
        observacao: formData.get('observacao')
    };

    try {
        const response = await fetch('/desinfeccoes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(desinfeccao)
        });

        if (response.ok) {
            event.target.reset();
            carregarDesinfeccoes();
            alert('Desinfecção registrada com sucesso!');
        } else {
            throw new Error('Erro ao salvar desinfecção');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao salvar desinfecção. Verifique o console para mais detalhes.');
    }
}

async function deletarDesinfeccao(id) {
    if (!confirm('Tem certeza que deseja excluir este registro?')) return;

    try {
        const response = await fetch(`/desinfeccoes/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            carregarDesinfeccoes();
            alert('Registro excluído com sucesso!');
        } else {
            throw new Error('Erro ao excluir registro');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao excluir registro. Verifique o console para mais detalhes.');
    }
}

// Fallback para modo offline
function salvarNoLocalStorage(desinfeccao) {
    if (typeof(Storage) !== "undefined") {
        let desinfeccoes = JSON.parse(localStorage.getItem('desinfeccoes') || '[]');
        desinfeccao.id = Date.now(); // ID temporário
        desinfeccoes.push(desinfeccao);
        localStorage.setItem('desinfeccoes', JSON.stringify(desinfeccoes));
        return true;
    }
    return false;
}

function carregarDoLocalStorage() {
    if (typeof(Storage) !== "undefined") {
        return JSON.parse(localStorage.getItem('desinfeccoes') || '[]');
    }
    return [];
}
