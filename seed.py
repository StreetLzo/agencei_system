from app import create_app
from extensions import db
from models.user import Usuario
from models.sala import Sala
from models.evento import Evento

from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta


def seed():
    app = create_app()

    with app.app_context():
        print("🔨 Criando tabelas...")
        db.create_all()

        # ===============================
        # 1️⃣ USUÁRIOS DE TESTE
        # ===============================
        usuarios = [
            {"nome": "Administrador Demo", "cpf": "00000000001", "senha": "admin123", "tipo": "admin"},
            {"nome": "Organizador Demo", "cpf": "00000000002", "senha": "org123", "tipo": "organizador"},
            {"nome": "Aluno Demo", "cpf": "00000000003", "senha": "aluno123", "tipo": "aluno"},
        ]

        for u in usuarios:
            if not Usuario.query.filter_by(cpf=u["cpf"]).first():
                usuario = Usuario(
                    nome=u["nome"],
                    cpf=u["cpf"],
                    tipo=u["tipo"],
                    ativo=True
                )
                usuario.senha = generate_password_hash(u["senha"])
                db.session.add(usuario)

        db.session.commit()
        print("👤 Usuários criados")

        organizador = Usuario.query.filter_by(tipo="organizador").first()

        # ===============================
        # 2️⃣ SALAS PRÉ-DEFINIDAS
        # ===============================
        salas_dados = [
            ("Auditório (TAMBAQUI)", 120),
            ("Laboratório de Informática", 40),
            ("Sala Treinamento (RIO BRANCO)", 30),
            ("Sala Treinamento (RIO MADEIRA)", 30),
            ("Sala Treinamento (RIO CANAÃ)", 30),
            ("Sala de Reunião (AÇAÍ)", 6),
            ("Sala de Reunião (JATOBÁ)", 6),
            ("Sala de Reunião (IPÊ)", 6),
            ("Sala de Reunião (CASTANHEIRA)", 6),
        ]

        salas = []

        for nome, capacidade in salas_dados:
            sala = Sala.query.filter_by(nome=nome).first()
            if not sala:
                sala = Sala(
                    nome=nome,
                    capacidade=capacidade,
                    ativa=True
                )
                db.session.add(sala)
            salas.append(sala)

        db.session.flush()
        print("🏠 Salas cadastradas")

        # ===============================
        # 3️⃣ EVENTO DE TESTE ETERNO
        # ===============================
        evento_existente = Evento.query.filter_by(
            nome_evento="Evento Permanente de Testes"
        ).first()

        if not evento_existente:
            evento = Evento(
                nome_evento="Evento Permanente de Testes",
                data_hora=None,   # 👈 ESSENCIAL
                duracao_horas=None,
                sala_id=salas[0].id,
                organizador_id=organizador.id,
                qr_code_link="EVENTO_PERMANENTE_TESTE"
            )
            db.session.add(evento)
            print("📅 Evento eterno criado")

        db.session.commit()
        print("✅ SEED FINALIZADO COM SUCESSO")


if __name__ == "__main__":
    seed()
