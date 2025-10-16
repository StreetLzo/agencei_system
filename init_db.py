# init_db.py

# Importar app, db e TODOS os modelos necessários
from app import app, db, Usuario, Sala, Evento, Inscricao
from datetime import datetime, timedelta
import os

# Define a função de inicialização
def init_db():
    # --- Mover a exclusão do arquivo para AQUI, fora do contexto do Flask ---
    if os.path.exists('agencei.db'):
        try:
            os.remove('agencei.db')
            print("Banco de dados antigo removido com sucesso.")
        except OSError as e:
            print(f"Erro ao remover agencei.db: {e}. Tente fechar qualquer programa que possa estar usando o arquivo (como um visualizador de SQLite).")
            return # Sai da função se a exclusão falhar
    # --------------------------------------------------------------------------------------

    with app.app_context():
        
        # 1. Cria todas as tabelas
        # Se a exclusão funcionou, db.create_all() criará um banco de dados vazio.
        db.create_all()
        print("Tabelas criadas com sucesso.")

        # 2. Insere Usuários de Teste (CPF/Senha = 123)
        user_organizador = Usuario(nome='Organizador Agencei', cpf='11111111111', senha='123', tipo='organizador')
        user_aluno = Usuario(nome='Aluno Teste', cpf='22222222222', senha='123', tipo='aluno')
        
        db.session.add_all([user_organizador, user_aluno])
        db.session.commit()
        print("Usuários de teste inseridos: Organizador (11111111111/123), Aluno (22222222222/123).")

        # 3. Insere Salas de Teste
        sala1 = Sala(nome='Auditório Tambaqui', capacidade=55)
        sala2 = Sala(nome='Auditório Ipê', capacidade=40)
        sala3 = Sala(nome='Auditório Tambaqui', capacidade=20)
        sala4 = Sala(nome='Sala de Reunião', capacidade=10)
        
        db.session.add_all([sala1, sala2, sala3, sala4])
        db.session.commit()
        print("Salas de teste inseridas.")
        
        # 4. Insere Eventos de Teste (Exemplo de evento futuro)
        data_evento = datetime.now() + timedelta(days=7) 
        
        evento_teste = Evento(
            nome_evento='Seminário de IA',
            data_hora=data_evento,
            duracao_horas=3.0,
            num_pessoas=0,
            sala_id=sala1.id,
            organizador_id=user_organizador.id,
            qr_code_link=f"AGENCEI_EVENTO_SEMINARIO_IA_{data_evento.strftime('%Y-%m-%d')}"
        )
        db.session.add(evento_teste)
        db.session.commit()
        print("Evento de teste inserido.")
        
        # 5. Inscreve o aluno no evento (para testar a rota 'meus_eventos')
        inscricao_teste = Inscricao(aluno_id=user_aluno.id, evento_id=evento_teste.id, status_presenca='Aguardando')
        db.session.add(inscricao_teste)
        db.session.commit()
        print("Aluno inscrito no evento de teste.")


if __name__ == '__main__':
    init_db()
