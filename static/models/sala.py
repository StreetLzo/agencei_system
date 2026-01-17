"""
Model: Sala
Representa as salas/locais disponíveis para eventos
"""
from extensions import db
from datetime import datetime


class Sala(db.Model):
    """
    Model para salas físicas do CEI
    """
    __tablename__ = 'sala'
    
    # Campos principais
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    capacidade = db.Column(db.Integer, nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    ativa = db.Column(db.Boolean, default=True)
    
    # Metadados
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    eventos = db.relationship('Evento', backref='sala', lazy=True)
    
    def __repr__(self):
        return f'<Sala {self.nome} (Cap: {self.capacidade})>'
    
    def tem_capacidade_para(self, num_pessoas):
        """Verifica se a sala comporta o número de pessoas"""
        return self.capacidade >= num_pessoas
    
    def esta_disponivel_em(self, data_hora, duracao_horas):
        """
        Verifica se a sala está disponível no horário solicitado
        Retorna: (disponivel: bool, evento_conflitante: Evento ou None)
        """
        from models.evento import Evento
        from datetime import timedelta
        
        fim_solicitado = data_hora + timedelta(hours=duracao_horas)
        
        # Buscar eventos da sala que possam conflitar
        eventos = Evento.query.filter_by(sala_id=self.id).all()
        
        for evento in eventos:
            evento_fim = evento.data_hora + timedelta(hours=evento.duracao_horas)
            
            # Verifica sobreposição: novo_inicio < evento_fim AND evento_inicio < novo_fim
            if data_hora < evento_fim and evento.data_hora < fim_solicitado:
                return False, evento
        
        return True, None
    
    @staticmethod
    def listar_disponiveis(data_hora, duracao_horas, capacidade_minima=0):
        """
        Lista todas as salas disponíveis para um horário específico
        """
        salas = Sala.query.filter(
            Sala.ativa == True,
            Sala.capacidade >= capacidade_minima
        ).all()
        
        salas_disponiveis = []
        for sala in salas:
            disponivel, _ = sala.esta_disponivel_em(data_hora, duracao_horas)
            if disponivel:
                salas_disponiveis.append(sala)
        
        return salas_disponiveis