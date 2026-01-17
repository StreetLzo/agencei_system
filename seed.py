from app import create_app
from extensions import db
from models.user import Usuario 
from werkzeug.security import generate_password_hash
from models.sala import Sala

def seed():
    # 1. Cria a aplicação
    app = create_app()
    
    # 2. Entra no contexto da aplicação (obrigatório para banco de dados)
    with app.app_context():
        print("🔨 Criando tabelas...")
        db.create_all()

        # 3. Cadastro de Usuários
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
                    ativo=True
                )
                novo_usuario.senha = generate_password_hash(u['senha'])
                db.session.add(novo_usuario)

        # 4. Cadastro de Salas
        salas = [
            {"nome": "Auditório A", "capacidade": 100, "descricao": "Espaço Principal"},
            {"nome": "Laboratório 01", "capacidade": 30, "descricao": "Informática"}
        ]

        for s in salas:
            if not Sala.query.filter_by(nome=s['nome']).first():
                print(f"🏠 Criando sala: {s['nome']}...")
                nova_sala = Sala(
                    nome=s['nome'],
                    capacidade=s['capacidade'],
                    descricao=s['descricao'],
                    ativa=True
                )
                db.session.add(nova_sala)
        
        # 5. Salva tudo de uma vez
        db.session.commit()
        print("✅ Seed finalizado com sucesso!")

# Este bloco apenas chama a função acima se o arquivo for executado diretamente
if __name__ == "__main__":
    seed()