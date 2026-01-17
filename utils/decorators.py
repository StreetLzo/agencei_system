"""
Decorators customizados para controle de acesso
"""
from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


def login_required_custom(f):
    """Garante que o usuário está logado."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('⚠️ Você precisa estar logado.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles, fallback_endpoint=None):
    """
    Garante que o usuário tem uma das roles especificadas.
    Se não tiver, redireciona para `fallback_endpoint` ou para login.
    
    Exemplo:
        @role_required('admin', fallback_endpoint='auth.login')
        @role_required('aluno', fallback_endpoint='aluno.eventos_disponiveis')
    """
    def decorator(f):
        @wraps(f)
        @login_required_custom
        def decorated(*args, **kwargs):
            if current_user.tipo not in roles:
                flash('❌ Você não tem permissão para acessar esta página.', 'error')
                # Se fallback definido, redireciona para lá
                if fallback_endpoint:
                    return redirect(url_for(fallback_endpoint))
                # Senão, vai para login
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated
    return decorator


def anonymous_required(redirect_map=None):
    """
    Garante que a rota só é acessível por usuários não logados.
    Se estiver logado, redireciona com base no role.
    Exemplo de redirect_map:
    {
        'admin': 'admin.dashboard',
        'organizador': 'organizador.salas',
        'aluno': 'aluno.eventos_disponiveis'
    }
    """
    redirect_map = redirect_map or {}

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if current_user.is_authenticated:
                for role, endpoint in redirect_map.items():
                    check_method = getattr(current_user, f'is_{role}', None)
                    if callable(check_method) and check_method():
                        return redirect(url_for(endpoint))
                # Caso role não esteja no mapa, envia para login por segurança
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated
    return decorator
