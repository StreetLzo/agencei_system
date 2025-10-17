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

        # 3. Insere Salas (Dados Reais)
        sala_tambaqui = Sala(nome='Auditório (TAMBAQUI)', capacidade=120)
        sala_laboratorio = Sala(nome='Laboratório de Informática', capacidade=40)
        sala_treinamento_rb = Sala(nome='Sala Treinamento (RIO BRANCO)', capacidade=30)
        sala_treinamento_rm = Sala(nome='Sala Treinamento (RIO MADEIRA)', capacidade=30)
        sala_treinamento_rc = Sala(nome='Sala Treinamento (RIO CANAÃ)', capacidade=30)
        sala_reuniao_acai = Sala(nome='Sala de Reunião (AÇAÍ)', capacidade=6)
        sala_reuniao_jatoba = Sala(nome='Sala de Reunião (JATOBÁ)', capacidade=6)
        sala_reuniao_ipe = Sala(nome='Sala de Reunião (IPÊ)', capacidade=6)
        sala_reuniao_castanheira = Sala(nome='Sala de Reunião (CASTANHEIRA)', capacidade=6)
        
        todas_salas = [
            sala_tambaqui, sala_laboratorio, sala_treinamento_rb, sala_treinamento_rm, 
            sala_treinamento_rc, sala_reuniao_acai, sala_reuniao_jatoba, 
            sala_reuniao_ipe, sala_reuniao_castanheira
        ]
        
        db.session.add_all(todas_salas)
        db.session.commit()
        print("Salas reais do CEI inseridas com sucesso.")
        
        # 4. Insere Eventos de Teste (Exemplo de evento futuro)
        data_evento = datetime.now() + timedelta(days=7) 
        
        evento_teste = Evento(
            nome_evento='Seminário de IA',
            data_hora=data_evento,
            duracao_horas=3.0,
            num_pessoas=0,
            # Associa o evento ao Auditório Tambaqui (sala de maior capacidade)
            sala_id=sala_tambaqui.id, 
            organizador_id=user_organizador.id,
            qr_code_link=f"AGENCEI_EVENTO_SEMINARIO_IA_{data_evento.strftime('%Y-%m-%d')}"
        )
        db.session.add(evento_teste)
        db.session.commit()
        print(f"Evento de teste inserido: '{evento_teste.nome_evento}' no {sala_tambaqui.nome}.")
        
        # 5. Inscreve o aluno no evento (para testar a rota 'meus_eventos')
        inscricao_teste = Inscricao(aluno_id=user_aluno.id, evento_id=evento_teste.id, status_presenca='Aguardando')
        db.session.add(inscricao_teste)
        db.session.commit()
        print("Aluno inscrito no evento de teste.")


if __name__ == '__main__':
    init_db()
