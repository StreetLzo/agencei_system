"""
Configurações da aplicação AGENCEI
"""
import os
from datetime import timedelta


class Config:
    """Configuração base da aplicação"""
    
    # Segurança
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    
    # Banco de dados
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///agencei.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # True em produção com HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # QR Code
    QR_CODE_JANELA_ANTES_MINUTOS = 30
    QR_CODE_JANELA_DEPOIS_MINUTOS = 30


class DevelopmentConfig(Config):
    """Configuração para desenvolvimento"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configuração para produção"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # Apenas HTTPS


class TestingConfig(Config):
    """Configuração para testes"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_agencei.db'
    WTF_CSRF_ENABLED = False


# Mapeamento de ambientes
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}