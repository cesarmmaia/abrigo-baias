from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from flask_cors import CORS
from app.models.database import Database
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__, template_folder='app/templates', static_folder='app/static', static_url_path='/static')
CORS(app)

# Configuração
app.config.from_pyfile('config.py')
app.secret_key = 'sua_chave_secreta_aqui'  # Para sessions

# Inicializar banco de dados
db = Database()

# Credenciais fixas (em produção, use banco de dados com hash)
USUARIO = 'aluno'
SENHA = 'aluno'

# Decorator para verificar autenticação
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logado' not in session:
            # Se for rota de API → devolve JSON
            if request.path.startswith('/api') or request.path.startswith('/desinfeccoes'):
                return jsonify({'error': 'Não autenticado'}), 401
            # Se for rota HTML → redireciona para login
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def verificar_credenciais(username, password):
    return username == USUARIO and password == SENHA

# Rotas de Autenticação
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if verificar_credenciais(username, password):
            session['logado'] = True
            session['usuario'] = username
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Credenciais inválidas!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você foi desconectado!', 'info')
    return redirect(url_for('login'))

# Rotas Protegidas - Páginas HTML
@app.route('/')
@login_required
def index():
    return render_template('index.html', usuario=session.get('usuario'))

@app.route('/agendamentos')
@login_required
def pagina_agendamentos():
    return render_template('agendamentos.html', usuario=session.get('usuario'))

@app.route('/relatorio')
@login_required
def pagina_relatorio():
    return render_template('relatorio.html', usuario=session.get('usuario'))

# Rotas para Desinfeccões (API)
@app.route('/desinfeccoes', methods=['GET'])
@login_required
def listar_desinfeccoes():
    try:
        desinfeccoes = db.get_all_desinfeccoes()
        return jsonify(desinfeccoes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/desinfeccoes', methods=['POST'])
@login_required
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
@login_required
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
@login_required
def deletar_desinfeccao(id):
    try:
        db.delete_desinfeccao(id)
        return jsonify({'message': 'Desinfecção deletada com sucesso'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rotas para Agendamentos (API)
@app.route('/api/agendamentos', methods=['GET'])
@login_required
def listar_agendamentos():
    try:
        agendamentos = db.get_all_agendamentos()
        return jsonify(agendamentos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agendamentos', methods=['POST'])
@login_required
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

@app.route('/api/agendamentos/<int:id>/status', methods=['PUT'])
@login_required
def atualizar_status_agendamento(id):
    try:
        data = request.get_json()
        db.update_agendamento_status(id, data['status'])
        return jsonify({'message': 'Status do agendamento atualizado com sucesso'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agendamentos/<int:id>', methods=['DELETE'])
@login_required
def deletar_agendamento(id):
    try:
        db.delete_agendamento(id)
        return jsonify({'message': 'Agendamento deletado com sucesso'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agendamentos/<int:id>/concluir', methods=['POST'])
@login_required
def concluir_agendamento(id):
    try:
        # Buscar todos e filtrar manualmente
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

# Rota para Relatório (API)
@app.route('/api/relatorio')
@login_required
def api_relatorio():
    try:
        desinfeccoes = db.get_all_desinfeccoes()
        
        if not desinfeccoes:
            return jsonify({'message': 'Nenhum registro de desinfecção encontrado'}), 200

        for desinfeccao in desinfeccoes:
            try:
                data_desinfeccao = datetime.strptime(desinfeccao['data_desinfeccao'], '%Y-%m-%d')
                dias_desde_desinfeccao = max(0, (datetime.now() - data_desinfeccao).days)

                if dias_desde_desinfeccao >= 15:
                    status = 'pendente'
                elif dias_desde_desinfeccao >= 10:
                    status = 'proximo'
                else:
                    status = 'ok'

                desinfeccao['dias_desde_desinfeccao'] = dias_desde_desinfeccao
                desinfeccao['status'] = status
                desinfeccao['data_formatada'] = data_desinfeccao.strftime('%d/%m/%Y')
            except ValueError as ve:
                print(f"Erro ao processar data: {desinfeccao['data_desinfeccao']} - {ve}")
                desinfeccao['dias_desde_desinfeccao'] = None
                desinfeccao['status'] = 'erro'
                desinfeccao['data_formatada'] = 'Data inválida'

        desinfeccoes_ordenadas = sorted(
            desinfeccoes,
            key=lambda x: (
                x['dias_desde_desinfeccao'] is not None,
                -x['dias_desde_desinfeccao'] if x['dias_desde_desinfeccao'] is not None else 0
            ),
            reverse=True
        )

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
    static_path = os.path.join(os.path.dirname(__file__), 'static')
    css_path = os.path.join(static_path, 'css', 'style.css')
    js_path = os.path.join(static_path, 'js', 'main.js')
    
    return f"""
    Static folder: {static_path}<br>
    CSS exists: {os.path.exists(css_path)}<br>
    JS exists: {os.path.exists(js_path)}<br>
    Current working directory: {os.getcwd()}
    """

@app.route('/debug-api')
def debug_api():
    try:
        desinfeccoes = db.get_all_desinfeccoes()
        agendamentos = db.get_all_agendamentos()
        
        return jsonify({
            'desinfeccoes_count': len(desinfeccoes),
            'agendamentos_count': len(agendamentos),
            'desinfeccoes_sample': desinfeccoes[:2] if desinfeccoes else [],
            'agendamentos_sample': agendamentos[:2] if agendamentos else []
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
