from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from app.models.database import Database
import os
from datetime import datetime, timedelta

app = Flask(__name__, template_folder='app/templates') #, static_folder='static', static_url_path='/static') #
CORS(app)

# Configuração
app.config.from_pyfile('config.py')

# Inicializar banco de dados
db = Database()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/agendamentos')
def pagina_agendamentos():
    return render_template('agendamentos.html')

@app.route('/relatorio')
def pagina_relatorio():
    return render_template('relatorio.html')

# Rotas para Desinfecções
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

# Rotas para Agendamentos
@app.route('/agendamentos', methods=['GET'])
def listar_agendamentos():
    try:
        agendamentos = db.get_all_agendamentos()
        return jsonify(agendamentos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/agendamentos', methods=['POST'])
def criar_agendamento():
    try:
        data = request.get_json()
        result = db.insert_agendamento(
            data['numero_baia'],
            data['data_agendamento'],
            data['metodo'],
            data.get('observacao', '')
        )
        return jsonify({'message': 'Agendamento criado com sucesso', 'id': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/agendamentos/<int:id>/status', methods=['PUT'])
def atualizar_status_agendamento(id):
    try:
        data = request.get_json()
        db.update_agendamento_status(id, data['status'])
        return jsonify({'message': 'Status do agendamento atualizado com sucesso'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/agendamentos/<int:id>', methods=['DELETE'])
def deletar_agendamento(id):
    try:
        db.delete_agendamento(id)
        return jsonify({'message': 'Agendamento deletado com sucesso'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/agendamentos/<int:id>/concluir', methods=['POST'])
def concluir_agendamento(id):
    try:
        # Buscar dados do agendamento
        agendamentos = db.get_all_agendamentos()
        agendamento = next((a for a in agendamentos if a['id'] == id), None)
        
        if not agendamento:
            return jsonify({'error': 'Agendamento não encontrado'}), 404
        
        # Criar desinfecção real
        result = db.insert_desinfeccao(
            agendamento['numero_baia'],
            datetime.now().strftime('%Y-%m-%d'),
            agendamento['metodo'],
            f"Agendamento concluído. Original: {agendamento.get('observacao', '')}"
        )
        
        # Atualizar status do agendamento
        db.update_agendamento_status(id, 'concluido')
        
        return jsonify({
            'message': 'Agendamento concluído e desinfecção registrada',
            'id_desinfeccao': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rota para Relatório
@app.route('/api/relatorio')
def api_relatorio():
    try:
        desinfeccoes = db.get_all_desinfeccoes()
        
        # Verificar se há registros
        if not desinfeccoes:
            return jsonify({'message': 'Nenhum registro de desinfecção encontrado'}), 200

        # Processar dados para relatório
        for desinfeccao in desinfeccoes:
            try:
                # Converter string para objeto datetime
                data_desinfeccao = datetime.strptime(desinfeccao['data_desinfeccao'], '%Y-%m-%d')
                
                # Calcular diferença de dias (apenas dias positivos)
                dias_desde_desinfeccao = max(0, (datetime.now() - data_desinfeccao).days)
                
                # Determinar status baseado nos dias
                if dias_desde_desinfeccao >= 15:
                    status = 'pendente'
                elif dias_desde_desinfeccao >= 10:
                    status = 'proximo'
                else:
                    status = 'ok'
                
                # Adicionar campos calculados
                desinfeccao['dias_desde_desinfeccao'] = dias_desde_desinfeccao
                desinfeccao['status'] = status
                desinfeccao['data_formatada'] = data_desinfeccao.strftime('%d/%m/%Y')
                
            except ValueError as ve:
                # Log de erro para data inválida
                print(f"Erro ao processar data: {desinfeccao['data_desinfeccao']} - {ve}")
                desinfeccao['dias_desde_desinfeccao'] = None
                desinfeccao['status'] = 'erro'
                desinfeccao['data_formatada'] = 'Data inválida'

        # Ordenar por data de desinfecção (mais recente primeiro)
        desinfeccoes_ordenadas = sorted(
            desinfeccoes,
            key=lambda x: (
                x['dias_desde_desinfeccao'] is not None,
                -x['dias_desde_desinfeccao'] if x['dias_desde_desinfeccao'] is not None else 0
            ),
            reverse=True
        )

        # Estatísticas para dashboard
        estatisticas = {
            'total': len(desinfeccoes_ordenadas),
            'ok': sum(1 for d in desinfeccoes_ordenadas if d.get('status') == 'ok'),
            'proximo': sum(1 for d in desinfeccoes_ordenadas if d.get('status') == 'proximo'),
            'pendente': sum(1 for d in desinfeccoes_ordenadas if d.get('status') == 'pendente'),
            'com_erro': sum(1 for d in desinfeccoes_ordenadas if d.get('status') == 'erro')
        }

        return jsonify({
            'estatisticas': estatisticas,
            'desinfeccoes': desinfeccoes_ordenadas
        })
        
    except Exception as e:
        print(f"Erro crítico em /api/relatorio: {e}")
        return jsonify({'error': 'Erro interno do servidor ao processar relatório'}), 500

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

if __name__ == '__main__':
    app.run(debug=True)