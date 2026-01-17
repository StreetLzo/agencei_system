"""
Model: Inscrição
Representa a relação entre alunos e eventos
"""
from extensions import db
from datetime import datetime


class Inscricao(db.Model):
    """
    Model para inscrições de alunos em eventos
    """
    __tablename__ = 'inscricao'
    
    # Campos principais
    id = db.Column(db.Integer, primary_key=True)
    status_presenca = db.Column(db.String(20), default='Aguardando', nullable=False)
    
    # Relacionamentos
    aluno_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=False)
    
    # Metadados
    inscrito_em = db.Column(db.DateTime, default=datetime.utcnow)
    presenca_confirmada_em = db.Column(db.DateTime, nullable=True)
    
    # Constraint de unicidade: um aluno não pode se inscrever duas vezes no mesmo evento
    __table_args__ = (
        db.UniqueConstraint('aluno_id', 'evento_id', name='_aluno_evento_uc'),
    )
    
    # Status possíveis
    STATUS_AGUARDANDO = 'Aguardando'
    STATUS_PRESENTE = 'Presente'
    STATUS_AUSENTE = 'Ausente'
    
    def __repr__(self):
        return f'<Inscricao Aluno:{self.aluno_id} Evento:{self.evento_id} Status:{self.status_presenca}>'
    
    def confirmar_presenca(self):
        """Marca a presença como confirmada"""
        self.status_presenca = self.STATUS_PRESENTE
        self.presenca_confirmada_em = datetime.utcnow()
        db.session.commit()
    
    def marcar_ausente(self):
        """Marca como ausente"""
        self.status_presenca = self.STATUS_AUSENTE
        db.session.commit()
    
    @property
    def esta_presente(self):
        """Verifica se a presença foi confirmada"""
        return self.status_presenca == self.STATUS_PRESENTE
    
    @staticmethod
    def aluno_ja_inscrito(aluno_id, evento_id):
        """Verifica se um aluno já está inscrito em um evento"""
        return Inscricao.query.filter_by(
            aluno_id=aluno_id,
            evento_id=evento_id
        ).first() is not None
    
    @staticmethod
    def contar_inscritos(evento_id):
        """Conta quantos alunos estão inscritos em um evento"""
        return Inscricao.query.filter_by(evento_id=evento_id).count()
    
    @staticmethod
    def contar_presentes(evento_id):
        """Conta quantas presenças foram confirmadas"""
        return Inscricao.query.filter_by(
            evento_id=evento_id,
            status_presenca=Inscricao.STATUS_PRESENTE
        ).count()
    
    @staticmethod
    def listar_por_aluno(aluno_id, apenas_futuros=False):
        """Lista todas as inscrições de um aluno"""
        from models.evento import Evento
        
        query = Inscricao.query.filter_by(aluno_id=aluno_id)
        
        if apenas_futuros:
            query = query.join(Evento).filter(Evento.data_hora >= datetime.now())
        
        return query.all()
    
    @staticmethod
    def listar_por_evento(evento_id):
        """Lista todas as inscrições de um evento"""
        return Inscricao.query.filter_by(evento_id=evento_id).all()