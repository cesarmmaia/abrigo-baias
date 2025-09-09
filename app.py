from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from app.models.database import Database
import os
from datetime import datetime
from datetime import timedelta
import sqlite3

app = Flask(__name__, template_folder='app/templates', static_folder='app/static',static_url_path='/static') # Mudei aqui.
CORS(app)

# Torna o datetime.now disponível como "now" nos templates
app.jinja_env.globals['now'] = datetime.now

# Configuração
app.config.from_pyfile('config.py')

# Inicializar banco de dados
db = Database()

@app.route('/')
def index():
    return render_template('index.html') # Mudei aqui.

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

@app.route('/relatorio')
def pagina_relatorio():
    return render_template('relatorio.html')


@app.route('/relatorio')
def relatorio():
    try:
        desinfeccoes = db.get_all_desinfeccoes()

        # Processar dados para relatório
        for desinfeccao in desinfeccoes:
            data_desinfeccao = datetime.strptime(desinfeccao['data_desinfeccao'], '%Y-%m-%d')
            dias_desde_desinfeccao = (datetime.now() - data_desinfeccao).days
            desinfeccao['dias_desde_desinfeccao'] = dias_desde_desinfeccao

            if dias_desde_desinfeccao >= 15:
                desinfeccao['status'] = 'pendente'
            elif dias_desde_desinfeccao >= 10:
                desinfeccao['status'] = 'proximo'
            else:
                desinfeccao['status'] = 'ok'

        return jsonify(desinfeccoes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/relatorio')
def api_relatorio():
    try:
        desinfeccoes = db.get_all_desinfeccoes()

        # Processar dados para relatório
        for desinfeccao in desinfeccoes:
            data_desinfeccao = datetime.strptime(desinfeccao['data_desinfeccao'], '%Y-%m-%d')
            dias_desde_desinfeccao = (datetime.now() - data_desinfeccao).days
            
            # 🔥 CORREÇÃO: Evitar valores negativos
            if dias_desde_desinfeccao < 0:
                # Se a data for futura, considerar como se fosse hoje
                dias_desde_desinfeccao = 0
                desinfeccao['status'] = 'ok'
            else:
                # Lógica normal para datas passadas
                if dias_desde_desinfeccao >= 15:
                    desinfeccao['status'] = 'pendente'
                elif dias_desde_desinfeccao >= 10:
                    desinfeccao['status'] = 'proximo'
                else:
                    desinfeccao['status'] = 'ok'

            desinfeccao['dias_desde_desinfeccao'] = dias_desde_desinfeccao

        #  CORREÇÃO: Ordenar por data mais recente primeiro
        desinfeccoes_ordenadas = sorted(
            desinfeccoes, 
            key=lambda x: x['data_desinfeccao'], 
            reverse=True
        )

        return jsonify(desinfeccoes_ordenadas)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/debug-static')
def debug_static():
    import os
    static_path = os.path.join(os.path.dirname(__file__), 'static')
    css_path = os.path.join(static_path, 'css', 'style.css')
    js_path = os.path.join(static_path, 'js', 'main.js')
    
    return f"""
    Static folder: {static_path}<br>
    CSS exists: {os.path.exists(css_path)}<br>
    JS exists: {os.path.exists(js_path)}<br>
    Current working directory: {os.getcwd()}
    """
# ... (código existente)

# NOVAS ROTAS PARA AGENDAMENTO (CORRIGIDAS)
@app.route('/api/agendamentos', methods=['GET'])
def listar_agendamentos():
    try:
        agendamentos = db.get_agendamentos_pendentes()
        return jsonify(agendamentos)
    except Exception as e:
        print(f"Erro ao listar agendamentos: {e}")  # Log para debug
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
        print(f"Erro ao criar agendamento: {e}")  # Log para debug
        return jsonify({'error': str(e)}), 500

@app.route('/api/agendamentos/<int:id>/realizar', methods=['POST'])
def realizar_agendamento(id):
    try:
        data = request.get_json()
        success = db.realizar_agendamento(id, data.get('data_realizacao'))
        if success:
            return jsonify({'message': 'Agendamento realizado com sucesso'})
        else:
            return jsonify({'error': 'Falha ao realizar agendamento'}), 400
    except Exception as e:
        print(f"Erro ao realizar agendamento: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/agendamentos/<int:id>', methods=['DELETE'])
def cancelar_agendamento(id):
    try:
        success = db.cancelar_agendamento(id)
        if success:
            return jsonify({'message': 'Agendamento cancelado com sucesso'})
        else:
            return jsonify({'error': 'Falha ao cancelar agendamento'}), 400
    except Exception as e:
        print(f"Erro ao cancelar agendamento: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/config/agendamento', methods=['GET'])
def get_config_agendamento():
    try:
        # Esta função precisa ser implementada no database.py
        intervalo = db.get_intervalo_agendamento()
        return jsonify({'intervalo_dias': intervalo})
    except Exception as e:
        print(f"Erro ao obter configuração: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/config/agendamento', methods=['POST'])
def update_config_agendamento():
    try:
        data = request.get_json()
        if not data or 'intervalo_dias' not in data:
            return jsonify({'error': 'Intervalo não especificado'}), 400
        
        success = db.update_config_agendamento(data['intervalo_dias']) 
        if success:
            return jsonify({'message': 'Configuração atualizada com sucesso'})
        else:
            return jsonify({'error': 'Falha ao atualizar configuração'}), 400
    except Exception as e:
        print(f"Erro ao atualizar configuração: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/proximo-agendamento/<int:numero_baia>')
def proximo_agendamento(numero_baia):
    try:
        proxima_data = db.get_proximo_agendamento(numero_baia)
        return jsonify({
            'numero_baia': numero_baia,
            'proxima_data': proxima_data.strftime('%Y-%m-%d') if proxima_data else None,
            'intervalo_dias': db.get_intervalo_agendamento()
        })
    except Exception as e:
        print(f"Erro ao obter próximo agendamento: {e}")
        return jsonify({'error': str(e)}), 500
@app.route('/agendamentos')
def pagina_agendamentos():
    return render_template('agendamentos.html')

# ... (código existente continua)

if __name__ == '__main__':
    app.run(debug=True)
