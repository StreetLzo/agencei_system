from app import create_app
from extensions import db
from models.user import Usuario 
from werkzeug.security import generate_password_hash
from models.sala import Sala
def seed():
    app = create_app()
    with app.app_context():
        print("🔨 Criando tabelas...")
        db.create_all()

        # Lista de usuários coringa
        users = [
            {
                "nome": "Administrador Demo",
                "cpf": "00000000001",
                "senha": "admin123",
                "tipo": "admin"
            },
            {
                "nome": "Organizador Demo",
                "cpf": "00000000002",
                "senha": "org123",
                "tipo": "organizador"
            },
            {
                "nome": "Aluno Demo",
                "cpf": "00000000003",
                "senha": "aluno123",
                "tipo": "aluno"
            }
        ]

        for u in users:
            existing_user = Usuario.query.filter_by(cpf=u['cpf']).first()
            if not existing_user:
                print(f"👤 Criando usuário: {u['nome']}...")
                
                # Criando a instância do usuário
                novo_usuario = Usuario(
                    nome=u['nome'],
                    cpf=u['cpf'],
                    tipo=u['tipo'],
                    ativo=True
                )
                
                # Se o seu modelo usa o campo 'senha' com hash:
                novo_usuario.senha = generate_password_hash(u['senha'])
                
                db.session.add(novo_usuario)
        
        db.session.commit()
        print("✅ Seed finalizado com sucesso!")
        
sala1 = Sala.query.filter_by(nome="Auditório A").first()
if not sala1:
    sala1 = Sala(nome="Auditório A", capacidade=100, descricao="Principal", ativa=True)
    db.session.add(sala1)
    db.session.commit()
if __name__ == "__main__":
    seed()