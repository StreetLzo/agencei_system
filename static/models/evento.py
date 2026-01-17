"""
Model: Evento
Representa os eventos/palestras/atividades agendadas
"""
from extensions import db
from datetime import datetime, timedelta
import hashlib


class Evento(db.Model):
    """
    Model para eventos do sistema
    """
    __tablename__ = 'evento'
    
    # Campos principais
    id = db.Column(db.Integer, primary_key=True)
    nome_evento = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    data_hora = db.Column(db.DateTime, nullable=False, index=True)
    duracao_horas = db.Column(db.Float, nullable=False)
    qr_code_link = db.Column(db.String(250), unique=True, nullable=False)
    
    # Relacionamentos
    sala_id = db.Column(db.Integer, db.ForeignKey('sala.id'), nullable=False)
    organizador_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    # Metadados
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    inscricoes = db.relationship('Inscricao', backref='evento', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Evento {self.nome_evento} em {self.data_hora.strftime("%d/%m/%Y")}>'
    
    @property
    def data_hora_fim(self):
        """Retorna a data/hora de término do evento"""
        return self.data_hora + timedelta(hours=self.duracao_horas)
    
    @property
    def num_inscritos(self):
        """Retorna o número de inscritos"""
        return len(self.inscricoes)
    
    @property
    def num_presentes(self):
        """Retorna o número de presenças confirmadas"""
        return sum(1 for i in self.inscricoes if i.status_presenca == 'Presente')
    
    def ja_iniciou(self):
        """Verifica se o evento já começou"""
        return datetime.now() >= self.data_hora
    
    def ja_terminou(self):
        """Verifica se o evento já terminou"""
        return datetime.now() >= self.data_hora_fim
    
    def esta_ativo(self):
        """Verifica se o evento está acontecendo agora"""
        return self.ja_iniciou() and not self.ja_terminou()
    
    def pode_confirmar_presenca(self, minutos_antes=30, minutos_depois=30):
        """
        Verifica se está na janela de confirmação de presença
        """
        agora = datetime.now()
        janela_inicio = self.data_hora - timedelta(minutes=minutos_antes)
        janela_fim = self.data_hora_fim + timedelta(minutes=minutos_depois)
        
        return janela_inicio <= agora <= janela_fim
    
    def pode_ser_excluido(self):
        """
        Verifica se o evento pode ser excluído
        Regra: apenas antes do término
        """
        return not self.ja_terminou()
    
    @staticmethod
    def gerar_qr_code(nome_evento, data_hora, sala_id, organizador_id):
        """
        Gera um código QR único e seguro para o evento
        """
        # Criar string única
        string_base = f"{nome_evento}_{data_hora.isoformat()}_{sala_id}_{organizador_id}"
        
        # Gerar hash SHA256
        hash_obj = hashlib.sha256(string_base.encode())
        hash_code = hash_obj.hexdigest()[:16]  # Primeiros 16 caracteres
        
        # Formato final
        qr_code = f"AGENCEI_{hash_code.upper()}"
        
        return qr_code
    
    def sala_tem_capacidade(self):
        """Verifica se a sala comporta os inscritos"""
        if not self.sala:
            return True
        return self.num_inscritos <= self.sala.capacidade
    
    @staticmethod
    def listar_disponiveis(apenas_futuros=True):
        """Lista eventos disponíveis para inscrição"""
        query = Evento.query
        
        if apenas_futuros:
            query = query.filter(Evento.data_hora >= datetime.now())
        
        return query.order_by(Evento.data_hora.asc()).all()