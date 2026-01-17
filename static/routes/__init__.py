"""
Routes package
Centraliza todos os blueprints da aplicação
"""
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.organizador import organizador_bp
from routes.aluno import aluno_bp

__all__ = [
    'auth_bp',
    'admin_bp',
    'organizador_bp',
    'aluno_bp'
]