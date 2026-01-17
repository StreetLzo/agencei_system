"""
AGENCEI - Sistema de Gerenciamento de Eventos
Arquivo principal da aplicação
"""
from flask import Flask, redirect, url_for
from config import Config
from extensions import db, login_manager


def create_app(config_class=Config):
    """
    Application Factory Pattern
    Cria e configura a aplicação Flask
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar extensões
    db.init_app(app)
    login_manager.init_app(app)

    # Configurar Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '⚠️ Você precisa estar logado para acessar esta página.'
    login_manager.login_message_category = 'warning'

    # Registrar blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.organizador import organizador_bp
    from routes.aluno import aluno_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(organizador_bp, url_prefix='/organizador')
    app.register_blueprint(aluno_bp, url_prefix='/aluno')

    # Rota raiz: envia usuário logado para a página correta ou para login
    @app.route('/')
    def index():
        from flask_login import current_user
        if current_user.is_authenticated:
            if current_user.is_admin():
                return redirect(url_for('admin.dashboard'))
            elif current_user.is_organizador():
                return redirect(url_for('organizador.salas'))
            elif current_user.is_aluno():
                return redirect(url_for('aluno.eventos_disponiveis'))
        return redirect(url_for('auth.login'))

    # User loader para Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from models.user import Usuario
        return Usuario.query.get(int(user_id))

    return app

app = create_app()
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # cria as tabelas que faltam
    app.run(debug=True)

