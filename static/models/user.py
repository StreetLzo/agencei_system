"""
Model: Usuário
Representa todos os tipos de usuários do sistema
"""
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class Usuario(UserMixin, db.Model):
    """
    Model para usuários do sistema
    Tipos: aluno, organizador, admin
    """
    __tablename__ = 'usuario'
    
    # Campos principais
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False, index=True)
    senha = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(20), nullable=False, default='aluno')
    
    # Metadados
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    eventos_criados = db.relationship('Evento', backref='organizador', lazy=True, foreign_keys='Evento.organizador_id')
    inscricoes = db.relationship('Inscricao', backref='aluno', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Usuario {self.nome} ({self.tipo})>'
    
    # Métodos para senha
    def set_password(self, senha):
        """Gera hash da senha"""
        self.senha = generate_password_hash(senha)
    
    def check_password(self, senha):
        """Verifica se a senha está correta"""
        return check_password_hash(self.senha, senha)
    
    # Métodos para Flask-Login
    def get_id(self):
        """Retorna o ID do usuário como string"""
        return str(self.id)
    
    @property
    def is_active(self):
        """Verifica se o usuário está ativo"""
        return self.ativo
    
    @property
    def is_authenticated(self):
        """Sempre True para usuários carregados"""
        return True
    
    @property
    def is_anonymous(self):
        """Sempre False para usuários reais"""
        return False
    
    # Métodos de verificação de tipo
    def is_admin(self):
        """Verifica se é administrador"""
        return self.tipo == 'admin'
    
    def is_organizador(self):
        """Verifica se é organizador"""
        return self.tipo == 'organizador'
    
    def is_aluno(self):
        """Verifica se é aluno"""
        return self.tipo == 'aluno'
    
    # Validação de CPF
    @staticmethod
    def validar_cpf(cpf):
        """
        Valida formato de CPF (apenas dígitos)
        Retorna True se válido
        """
        cpf = ''.join(filter(str.isdigit, cpf))
        
        if len(cpf) != 11:
            return False
        
        # Verifica se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            return False
        
        # Validação dos dígitos verificadores
        def calcular_digito(cpf_parcial, pesos):
            soma = sum(int(cpf_parcial[i]) * pesos[i] for i in range(len(pesos)))
            resto = soma % 11
            return 0 if resto < 2 else 11 - resto
        
        pesos_primeiro = list(range(10, 1, -1))
        pesos_segundo = list(range(11, 1, -1))
        
        digito1 = calcular_digito(cpf[:9], pesos_primeiro)
        digito2 = calcular_digito(cpf[:10], pesos_segundo)
        
        return cpf[-2:] == f'{digito1}{digito2}'