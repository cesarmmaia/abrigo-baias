import pytest
from datetime import datetime, timedelta
from app import app
from app.models.database import Database

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_calculo_status_desinfeccao():
    """Testa o cálculo correto do status baseado na data"""
    from app import app

    with app.app_context():
        # Teste para status "ok" (menos de 10 dias)
        data_recente = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        assert calcular_status(data_recente) == 'ok'

        # Teste para status "próximo" (10-14 dias)
        data_proxima = (datetime.now() - timedelta(days=12)).strftime('%Y-%m-%d')
        assert calcular_status(data_proxima) == 'proximo'

        # Teste para status "pendente" (15+ dias)
        data_pendente = (datetime.now() - timedelta(days=16)).strftime('%Y-%m-%d')
        assert calcular_status(data_pendente) == 'pendente'

def calcular_status(data_desinfeccao):
    """Função auxiliar para cálculo de status (simula a lógica do frontend)"""
    from datetime import datetime

    data_desinfeccao = datetime.strptime(data_desinfeccao, '%Y-%m-%d')
    dias_desde_desinfeccao = (datetime.now() - data_desinfeccao).days

    if dias_desde_desinfeccao >= 15:
        return 'pendente'
    elif dias_desde_desinfeccao >= 10:
        return 'proximo'
    else:
        return 'ok'
