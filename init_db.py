from app import create_app
from extensions import db
from models import User, Sala, Evento, Inscricao
from datetime import datetime, timedelta
import os

def init_db():
    # --- RESET DO BANCO (DEV ONLY) ---
    if os.path.exists('agencei.db'):
        os.remove('agencei.db')
        print("Banco antigo removido.")

    app = create_app()

    with app.app_context():
        # 1️⃣ Criação das tabelas
        db.create_all()
        print("Tabelas criadas.")

        # 2️⃣ Usuários base
        admin = User(
            nome="Administrador CEI",
            cpf="00000000000",
            senha="hash_aqui",
            role="admin"
        )

        organizador = User(
            nome="Organizador Agencei",
            cpf="11111111111",
            senha="hash_aqui",
            role="organizador"
        )

        aluno = User(
            nome="Aluno Teste",
            cpf="22222222222",
            senha="hash_aqui",
            role="aluno"
        )

        db.session.add_all([admin, organizador, aluno])
        db.session.commit()

        # 3️⃣ Salas reais do CEI
        salas = [
            Sala(nome="Auditório (TAMBAQUI)", capacidade=120),
            Sala(nome="Laboratório de Informática", capacidade=40),
            Sala(nome="Sala Treinamento (RIO BRANCO)", capacidade=30),
            Sala(nome="Sala Treinamento (RIO MADEIRA)", capacidade=30),
            Sala(nome="Sala Treinamento (RIO CANAÃ)", capacidade=30),
            Sala(nome="Sala de Reunião (AÇAÍ)", capacidade=6),
            Sala(nome="Sala de Reunião (JATOBÁ)", capacidade=6),
            Sala(nome="Sala de Reunião (IPÊ)", capacidade=6),
            Sala(nome="Sala de Reunião (CASTANHEIRA)", capacidade=6),
        ]

        db.session.add_all(salas)
        db.session.commit()

        # 4️⃣ Evento de teste
        evento = Evento(
            nome_evento="Seminário de IA",
            data_hora=datetime.now() + timedelta(days=7),
            duracao_horas=3,
            sala_id=salas[0].id,
            organizador_id=organizador.id,
            qr_code_link="AGENCEI_EVENTO_SEMINARIO_IA"
        )

        db.session.add(evento)
        db.session.commit()

        # 5️⃣ Inscrição teste
        inscricao = Inscricao(
            aluno_id=aluno.id,
            evento_id=evento.id,
            status_presenca="Aguardando"
        )

        db.session.add(inscricao)
        db.session.commit()

        print("Banco inicializado com dados reais do CEI.")

if __name__ == "__main__":
    init_db()
