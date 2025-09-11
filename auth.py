from flask import session, redirect, url_for, request, flash
from functools import wraps

# Credenciais fixas (em produção, use banco de dados com hash)
USUARIO = 'admin'
SENHA = 'admin'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logado' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def verificar_credenciais(username, password):
    return username == USUARIO and password == SENHA