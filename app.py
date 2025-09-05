from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from app.models.database import Database
import os
from datetime import datetime, timedelta

app = Flask(__name__, template_folder='app/templates', static_folder='app/static',static_url_path='/static') # Mudei aqui.
CORS(app)

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
