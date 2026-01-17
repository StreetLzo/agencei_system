from app import create_app
from extensions import db
from models.user import Usuario
from models.sala import Sala
from werkzeug.security import generate_password_hash

def seed():
    app = create_app()
    with app.app_context():
        print("🔨 Inicializando banco de dados...")
        # Cria as tabelas se elas não existirem
        db.create_all()

        # 1. Cadastro de Usuários Coringa
        users = [
            {"nome": "Administrador Demo", "cpf": "00000000001", "senha": "admin123", "tipo": "admin"},
            {"nome": "Organizador Demo", "cpf": "00000000002", "senha": "org123", "tipo": "organizador"},
            {"nome": "Aluno Demo", "cpf": "00000000003", "senha": "aluno123", "tipo": "aluno"}
        ]

        for u in users:
            if not Usuario.query.filter_by(cpf=u['cpf']).first():
                print(f"👤 Criando usuário: {u['nome']}...")
                novo_usuario = Usuario(
                    nome=u['nome'],
                    cpf=u['cpf'],
                    tipo=u['tipo'],
                    ativa=True # Verifique se no seu modelo Usuario o campo é 'ativo' ou 'ativa'
                )
                novo_usuario.senha = generate_password_hash(u['senha'])
                db.session.add(novo_usuario)

        # 2. Cadastro de Salas Coringa (Baseado no seu modelo Sala)
        salas_demo = [
            {
                "nome": "Auditório Principal", 
                "capacidade": 150, 
                "descricao": "Espaço amplo para palestras e seminários",
                "ativa": True
            },
            {
                "nome": "Laboratório de Informática", 
                "capacidade": 40, 
                "descricao": "Equipado com computadores e projetor",
                "ativa": True
            },
            {
                "nome": "Sala de Reuniões 01", 
                "capacidade": 15, 
                "descricao": "Ideal para grupos de trabalho menores",
                "ativa": True
            }
        ]

        for s in salas_demo:
            if not Sala.query.filter_by(nome=s['nome']).first():
                print(f"🏠 Criando sala: {s['nome']}...")
                nova_sala = Sala(
                    nome=s['nome'],
                    capacidade=s['capacidade'],
                    descricao=s['descricao'],
                    ativa=s['ativa']
                )
                db.session.add(nova_sala)
        
        try:
            db.session.commit()
            print("✅ Seed finalizado com sucesso!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao salvar dados: {str(e)}")

if __name__ == "__main__":
    seed()