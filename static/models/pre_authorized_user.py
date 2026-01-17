"""
Model: PreAuthorizedUser
Gerencia CPFs autorizados para cadastro de organizadores
"""
from extensions import db
from datetime import datetime


class PreAuthorizedUser(db.Model):
    """
    Model para CPFs pré-autorizados (apenas organizadores)
    """
    __tablename__ = 'pre_authorized_user'
    
    # Campos principais
    id = db.Column(db.Integer, primary_key=True)
    cpf = db.Column(db.String(11), unique=True, nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default='organizador')
    ativo = db.Column(db.Boolean, default=True)
    usado = db.Column(db.Boolean, default=False)
    
    # Metadados
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    usado_em = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        status = "Usado" if self.usado else "Disponível"
        return f'<PreAuth CPF:{self.cpf} Role:{self.role} {status}>'
    
    def marcar_como_usado(self):
        """Marca o CPF como já utilizado"""
        self.usado = True
        self.usado_em = datetime.utcnow()
        db.session.commit()
    
    def desativar(self):
        """Desativa o CPF autorizado"""
        self.ativo = False
        db.session.commit()
    
    def reativar(self):
        """Reativa o CPF autorizado"""
        self.ativo = True
        db.session.commit()
    
    @staticmethod
    def cpf_autorizado(cpf, role='organizador'):
        """
        Verifica se um CPF está autorizado para cadastro
        Retorna o objeto PreAuthorizedUser se válido, None caso contrário
        """
        pre_auth = PreAuthorizedUser.query.filter_by(
            cpf=cpf,
            role=role,
            ativo=True,
            usado=False
        ).first()
        
        return pre_auth
    
    @staticmethod
    def criar_autorizacao(cpf, role='organizador', criado_por_id=None):
        """
        Cria uma nova autorização de CPF
        """
        # Verifica se já existe
        existe = PreAuthorizedUser.query.filter_by(cpf=cpf).first()
        if existe:
            return None, "CPF já está cadastrado no sistema de autorizações"
        
        # Validar CPF
        from models.user import Usuario
        if not Usuario.validar_cpf(cpf):
            return None, "CPF inválido"
        
        # Verificar se já é usuário
        usuario_existe = Usuario.query.filter_by(cpf=cpf).first()
        if usuario_existe:
            return None, "CPF já possui cadastro no sistema"
        
        # Criar autorização
        pre_auth = PreAuthorizedUser(
            cpf=cpf,
            role=role,
            criado_por=criado_por_id
        )
        
        db.session.add(pre_auth)
        db.session.commit()
        
        return pre_auth, "Autorização criada com sucesso"
    
    @staticmethod
    def listar_todos(apenas_ativos=False, apenas_disponiveis=False):
        """Lista todas as autorizações"""
        query = PreAuthorizedUser.query
        
        if apenas_ativos:
            query = query.filter_by(ativo=True)
        
        if apenas_disponiveis:
            query = query.filter_by(usado=False)
        
        return query.order_by(PreAuthorizedUser.criado_em.desc()).all()