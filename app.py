from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from app.models.database import Database
import os
from datetime import datetime

app = Flask(__name__, template_folder='app/templates', static_folder='app/static', static_url_path='/static')
CORS(app)

# Torna o datetime.now disponível como "now" nos templates
app.jinja_env.globals['now'] = datetime.now

# Configuração
app.config.from_pyfile('config.py')

# Inicializar banco de dados
db = Database()

@app.route('/')
def index():
    return render_template('index.html')


# ================== ROTAS DE DESINFECÇÃO ==================
@app.route('/desinfeccoes', methods=['GET'])
def listar_desinfeccoes():
    try:
        desinfeccoes = db.get_all_desinfeccoes()
        return jsonify(desinfeccoes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/desinfeccoes', methods=['POST'])
def criar_desinfeccao():
    try:
        data = request.get_json()
        if not data or 'numero_baia' not in data or 'data_desinfeccao' not in data or 'metodo' not in data:
            return jsonify({'error': 'Dados incompletos'}), 400

        result = db.insert_desinfeccao(
            data['numero_baia'],
            data['data_desinfeccao'],
            data['metodo'],
            data.get('observacao', '')
        )
        return jsonify({'message': 'Desinfecção registrada com sucesso', 'id': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/desinfeccoes/<int:id>', methods=['PUT'])
def atualizar_desinfeccao(id):
    try:
        data = request.get_json()
        db.update_desinfeccao(
            id,
            data['numero_baia'],
            data['data_desinfeccao'],
            data['metodo'],
            data.get('observacao', '')
        )
        return jsonify({'message': 'Desinfecção atualizada com sucesso'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/desinfeccoes/<int:id>', methods=['DELETE'])
def deletar_desinfeccao(id):
    try:
        db.delete_desinfeccao(id)
        return jsonify({'message': 'Desinfecção deletada com sucesso'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ================== ROTAS DE RELATÓRIO ==================
@app.route('/relatorio')
def pagina_relatorio():
    return render_template('relatorio.html')


@app.route('/api/relatorio')
def api_relatorio():
    try:
        desinfeccoes = db.get_all_desinfeccoes()
        for desinfeccao in desinfeccoes:
            data_desinfeccao = datetime.strptime(desinfeccao['data_desinfeccao'], '%Y-%m-%d')
            dias_desde = (datetime.now() - data_desinfeccao).days
            desinfeccao['dias_desde_desinfeccao'] = max(0, dias_desde)

            if dias_desde >= 15:
                desinfeccao['status'] = 'pendente'
            elif dias_desde >= 10:
                desinfeccao['status'] = 'proximo'
            else:
                desinfeccao['status'] = 'ok'

        return jsonify(desinfeccoes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ================== ROTAS DE AGENDAMENTO ==================
@app.route('/api/agendamentos', methods=['GET'])
def listar_agendamentos():
    try:
        agendamentos = db.get_agendamentos_pendentes()
        return jsonify(agendamentos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/agendamentos', methods=['POST'])
def criar_agendamento():
    try:
        data = request.get_json()
        if not data or 'numero_baia' not in data or 'data_agendamento' not in data or 'metodo' not in data:
            return jsonify({'error': 'Dados incompletos'}), 400

        result = db.criar_agendamento(
            data['numero_baia'],
            data['data_agendamento'],
            data['metodo'],
            data.get('observacao', '')
        )
        return jsonify({'message': 'Agendamento criado com sucesso', 'id': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/agendamentos/<int:id>/realizar', methods=['POST'])
def realizar_agendamento(id):
    try:
        data = request.get_json() or {}
        success = db.realizar_agendamento(id, data.get('data_realizacao'))
        if success:
            return jsonify({'message': 'Agendamento realizado com sucesso'})
        else:
            return jsonify({'error': 'Agendamento não encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/agendamentos/<int:id>', methods=['DELETE'])
def cancelar_agendamento(id):
    try:
        success = db.cancelar_agendamento(id)
        if success:
            return jsonify({'message': 'Agendamento cancelado com sucesso'})
        else:
            return jsonify({'error': 'Agendamento não encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/agendamentos')
def pagina_agendamentos():
    return render_template('agendamentos.html')


if __name__ == '__main__':
    app.run(debug=True)
