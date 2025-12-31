# app.py (REVISADO)
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from werkzeug.security import generate_password_hash, check_password_hash
import os

# --- Configurações iniciais ---
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agencei.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# usar variável de ambiente para segurança, com fallback (somente para dev)
app.secret_key = os.environ.get('SECRET_KEY', 'sua_chave_secreta_aqui')

db = SQLAlchemy(app)

# --- Modelos ---
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    senha = db.Column(db.String(128), nullable=False)  # espaço para hash
    tipo = db.Column(db.String(10), nullable=False)
    eventos_criados = db.relationship('Evento', backref='organizador', lazy=True)
    inscricoes = db.relationship('Inscricao', backref='aluno', lazy=True, cascade="all, delete-orphan")

class Sala(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    capacidade = db.Column(db.Integer, nullable=False)
    eventos = db.relationship('Evento', backref='sala', lazy=True)

class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_evento = db.Column(db.String(150), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False)
    duracao_horas = db.Column(db.Float, nullable=False)
    num_pessoas = db.Column(db.Integer, nullable=False, default=0)
    qr_code_link = db.Column(db.String(250), nullable=True)  # Valor interno para QR Code e validação

    sala_id = db.Column(db.Integer, db.ForeignKey('sala.id'), nullable=False)
    organizador_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

    inscricoes = db.relationship('Inscricao', backref='evento', lazy=True, cascade="all, delete-orphan")

class Inscricao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status_presenca = db.Column(db.String(20), default='Aguardando')
    aluno_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('aluno_id', 'evento_id', name='_aluno_evento_uc'),)


# --- Rotas de autenticação ---
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cpf = request.form.get('cpf')
        senha = request.form.get('senha')
        usuario = Usuario.query.filter_by(cpf=cpf).first()

        if usuario and check_password_hash(usuario.senha, senha):
            session['logged_in'] = True
            session['user_id'] = usuario.id
            session['user_nome'] = usuario.nome
            session['user_tipo'] = usuario.tipo
            flash(f'Bem-vindo(a), {usuario.nome}!', 'success')

            # Redirecionar para a página salva após login/cadastro, se houver
            next_url = session.pop('next_url', None)
            if next_url:
                return redirect(next_url)

            return redirect(url_for('home'))
        else:
            flash('CPF ou Senha incorretos.', 'error')

    # Se houver um 'next_url' nos parâmetros, manter na sessão para pós-login
    if 'next_url' in request.args:
        session['next_url'] = request.args['next_url']

    return render_template('login.html')


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome')
        cpf = request.form.get('cpf')
        senha = request.form.get('senha')
        tipo = request.form.get('tipo')

        # validações básicas
        if not (nome and cpf and senha and tipo):
            flash('Por favor, preencha todos os campos.', 'error')
            return render_template('cadastro.html')

        if Usuario.query.filter_by(cpf=cpf).first():
            flash('❌ Já existe uma conta registrada com este CPF.', 'error')
            return render_template('cadastro.html')

        # armazenar senha como hash
        senha_hash = generate_password_hash(senha)
        novo_usuario = Usuario(nome=nome, cpf=cpf, senha=senha_hash, tipo=tipo)

        try:
            db.session.add(novo_usuario)
            db.session.commit()
            flash('✅ Conta criada com sucesso! Faça login.', 'success')

            # Redirecionar para a página salva após login/cadastro, se houver
            next_url = session.pop('next_url', None)
            if next_url:
                return redirect(next_url)

            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar conta: {e}', 'error')

    return render_template('cadastro.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('user_nome', None)
    session.pop('user_tipo', None)
    session.pop('next_url', None)  # Limpar next_url ao fazer logout
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('login'))


# --- Hub principal ---
@app.route('/home')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_tipo = session.get('user_tipo')

    if user_tipo == 'organizador':
        return redirect(url_for('organizador_salas'))
    elif user_tipo == 'aluno':
        return redirect(url_for('aluno_eventos_disponiveis'))

    return render_template('home.html')



# --- Rotas do Organizador ---
@app.route('/organizador/salas')
def organizador_salas():
    if session.get('user_tipo') != 'organizador':
        return redirect(url_for('login'))

    salas = Sala.query.order_by(Sala.capacidade.desc()).all()
    return render_template('organizador_salas.html', salas=salas)


@app.route('/reservar/<int:sala_id>', methods=['GET', 'POST'])
def reservar_sala(sala_id):
    if session.get('user_tipo') != 'organizador':
        return redirect(url_for('login'))

    sala = Sala.query.get_or_404(sala_id)

    if request.method == 'POST':
        nome_evento = request.form.get('nome_evento')
        data_str = request.form.get('data')
        hora_str = request.form.get('hora')
        try:
            duracao = float(request.form.get('duracao'))
            num_pessoas = int(request.form.get('num_pessoas'))
        except (TypeError, ValueError):
            flash('Duração ou número de pessoas inválidos.', 'error')
            return render_template('organizador_reserva.html', sala=sala)

        if num_pessoas > sala.capacidade:
            flash('O número de pessoas excede a capacidade da sala.', 'error')
            return render_template('organizador_reserva.html', sala=sala)

        data_hora_str = f"{data_str} {hora_str}"
        try:
            data_hora = datetime.strptime(data_hora_str, '%Y-%m-%d %H:%M')
            data_fim = data_hora + timedelta(hours=duracao)
        except ValueError:
            flash('Formato de Data ou Hora inválido. Use AAAA-MM-DD e HH:MM.', 'error')
            return render_template('organizador_reserva.html', sala=sala)

        # Para evitar complexidade com expressão SQL envolvendo timedelta, trazemos os eventos da sala
        # e checamos sobreposição em Python (mais simples e portátil)
        eventos_na_sala = Evento.query.filter_by(sala_id=sala_id).all()
        conflito = None
        for ev in eventos_na_sala:
            ev_inicio = ev.data_hora
            ev_fim = ev.data_hora + timedelta(hours=ev.duracao_horas)
            # sobreposição: novo_inicio < ev_fim and ev_inicio < novo_fim
            if (data_hora < ev_fim) and (ev_inicio < data_fim):
                conflito = ev
                break

        if conflito:
            flash('❌ Conflito de horário! A sala já está reservada neste período.', 'error')
            return render_template('organizador_reserva.html', sala=sala)

        # gerar qr_code_link simples e único
        qr_code_link = f"AGENCEI_EVENTO_{nome_evento.replace(' ', '_').upper()}_{data_hora.strftime('%Y%m%d%H%M')}_{sala_id}"

        novo_evento = Evento(
            nome_evento=nome_evento,
            data_hora=data_hora,
            duracao_horas=duracao,
            num_pessoas=num_pessoas,
            sala_id=sala_id,
            organizador_id=session['user_id'],
            qr_code_link=qr_code_link
        )

        db.session.add(novo_evento)
        db.session.commit()

        flash('✅ Sua reserva foi registrada com sucesso!', 'success')
        return redirect(url_for('minhas_reservas'))

    return render_template('organizador_reserva.html', sala=sala)


@app.route('/organizador/reservas')
def minhas_reservas():
    if session.get('user_tipo') != 'organizador':
        return redirect(url_for('login'))

    eventos = Evento.query.filter_by(organizador_id=session['user_id']).order_by(Evento.data_hora.asc()).all()

    eventos_data = []
    for evento in eventos:
        sala = db.session.get(Sala, evento.sala_id)
        num_inscritos = Inscricao.query.filter_by(evento_id=evento.id).count()

        evento_fim = evento.data_hora + timedelta(hours=evento.duracao_horas)
        pode_excluir = datetime.now() < evento_fim

        eventos_data.append({
            'id': evento.id,
            'nome': evento.nome_evento,
            'data_hora': evento.data_hora.strftime('%d/%m/%Y às %H:%M'),
            'duracao': evento.duracao_horas,
            'num_pessoas': evento.num_pessoas,
            'local': sala.nome if sala else '—',
            'inscritos': num_inscritos,
            'pode_excluir': pode_excluir,
            'link_inscricao': url_for('inscrever_evento', evento_id=evento.id, _external=True)  # Link para compartilhamento
        })

    return render_template('organizador_minhas_reservas.html', eventos=eventos_data)


@app.route('/organizador/reservas/excluir/<int:evento_id>', methods=['POST'])
def excluir_reserva(evento_id):
    if session.get('user_tipo') != 'organizador':
        return redirect(url_for('login'))

    evento = Evento.query.get_or_404(evento_id)

    evento_fim = evento.data_hora + timedelta(hours=evento.duracao_horas)
    if datetime.now() >= evento_fim:
        flash('❌ Não é possível excluir uma reserva que já foi concluída ou iniciada.', 'error')
        return redirect(url_for('minhas_reservas'))

    try:
        db.session.delete(evento)
        db.session.commit()
        flash(f'✅ Reserva "{evento.nome_evento}" excluída com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir reserva: {e}', 'error')

    return redirect(url_for('minhas_reservas'))


@app.route('/organizador/participantes/<int:evento_id>')
def lista_participantes(evento_id):
    if session.get('user_tipo') != 'organizador':
        return redirect(url_for('login'))

    evento = Evento.query.get_or_404(evento_id)
    inscricoes = Inscricao.query.filter_by(evento_id=evento_id).all()

    participantes_data = []
    for inscricao in inscricoes:
        aluno = Usuario.query.get(inscricao.aluno_id)
        participantes_data.append({
            'nome': aluno.nome if aluno else '—',
            'cpf': aluno.cpf if aluno else '—',
            'status': inscricao.status_presenca
        })

    qr_code_value = evento.qr_code_link

    return render_template(
        'organizador_lista_participantes.html',
        evento=evento,
        participantes=participantes_data,
        qr_code_value=qr_code_value
    )


# --- Rotas do Aluno ---
@app.route('/aluno/eventos')
def aluno_eventos_disponiveis():
    if session.get('user_tipo') != 'aluno':
        return redirect(url_for('login'))

    eventos = Evento.query.filter(Evento.data_hora >= datetime.now()).order_by(Evento.data_hora.asc()).all()

    eventos_data = []
    for evento in eventos:
        sala = Sala.query.get(evento.sala_id)
        inscrito = Inscricao.query.filter_by(aluno_id=session.get('user_id'), evento_id=evento.id).first()

        eventos_data.append({
            'id': evento.id,
            'nome': evento.nome_evento,
            'local': sala.nome if sala else '—',
            'capacidade': sala.capacidade if sala else 0,
            'num_pessoas': evento.num_pessoas,
            'data_hora': evento.data_hora.strftime('%d/%m/%Y às %H:%M'),
            'inscrito': 'Sim' if inscrito else 'Não'
        })

    return render_template('aluno_eventos_disponiveis.html', eventos=eventos_data)


# Rota de Inscrição (com lógica para link direto e redirecionamento)
@app.route('/aluno/inscrever/<int:evento_id>')
def inscrever_evento(evento_id):
    if not session.get('logged_in'):
        flash('⚠️ Você precisa estar logado para se inscrever.', 'warning')
        # Salva o URL para redirecionar após login/cadastro
        session['next_url'] = url_for('confirmar_inscricao', evento_id=evento_id, _external=True)
        return redirect(url_for('login'))

    if session.get('user_tipo') != 'aluno':
        flash('❌ Apenas alunos podem se inscrever em eventos.', 'error')
        return redirect(url_for('home'))  # Ou para uma página de erro

    return redirect(url_for('confirmar_inscricao', evento_id=evento_id))


# Confirmar inscrição
@app.route('/aluno/confirmar_inscricao/<int:evento_id>')
def confirmar_inscricao(evento_id):
    if not session.get('logged_in') or session.get('user_tipo') != 'aluno':
        flash('Erro: Acesso negado para inscrição.', 'error')
        return redirect(url_for('login'))

    evento = Evento.query.get_or_404(evento_id)
    aluno_id = session['user_id']

    ja_inscrito = Inscricao.query.filter_by(aluno_id=aluno_id, evento_id=evento.id).first()
    if ja_inscrito:
        flash('⚠️ Você já está inscrito neste evento.', 'warning')
        return redirect(url_for('meus_eventos'))

    # verificar capacidade
    inscritos_count = Inscricao.query.filter_by(evento_id=evento.id).count()
    # se quiser respeitar uma capacidade máxima, comente/descomente a verificação abaixo:
    sala = Sala.query.get(evento.sala_id)
    if sala and inscritos_count >= sala.capacidade:
        flash('❌ Não há vagas disponíveis neste evento.', 'error')
        return redirect(url_for('aluno_eventos_disponiveis'))

    nova_inscricao = Inscricao(aluno_id=aluno_id, evento_id=evento.id, status_presenca='Aguardando')
    db.session.add(nova_inscricao)

    # opcional: atualizar contador num_pessoas (se essa coluna for usada como contador)
    try:
        evento.num_pessoas = (evento.num_pessoas or 0) + 1
        db.session.commit()
        flash('✅ Inscrição realizada com sucesso! Bom evento.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao efetuar inscrição: {e}', 'error')

    return redirect(url_for('meus_eventos'))


@app.route('/aluno/meus_eventos')
def meus_eventos():
    if session.get('user_tipo') != 'aluno':
        return redirect(url_for('login'))

    inscricoes = Inscricao.query.filter_by(aluno_id=session['user_id']).all()

    eventos_data = []
    # ordenar por data do evento em Python (pois Inscricao não tem a coluna data_hora)
    inscricoes_validas = []
    for inscr in inscricoes:
        evento = Evento.query.get(inscr.evento_id)
        if evento:
            inscricoes_validas.append((inscr, evento))

    inscricoes_validas.sort(key=lambda pair: pair[1].data_hora)  # ordena por evento.data_hora

    for inscr, evento in inscricoes_validas:
        sala = Sala.query.get(evento.sala_id)
        eventos_data.append({
            'id': evento.id,
            'nome': evento.nome_evento,
            'local': sala.nome if sala else '—',
            'data_hora': evento.data_hora.strftime('%d/%m/%Y às %H:%M'),
            'status_presenca': inscr.status_presenca
        })

    return render_template('aluno_meus_eventos.html', eventos=eventos_data)


# Rota: Escanear QR Code (Interface com Câmera)
@app.route('/aluno/escanear', methods=['GET'])
def escanear_qr_code():
    if session.get('user_tipo') != 'aluno':
        return redirect(url_for('login'))

    return render_template('aluno_escanear_qr.html')


# Rota: Confirmação de Presença
@app.route('/aluno/confirmar_presenca', methods=['POST'])
def confirmar_presenca():
    if session.get('user_tipo') != 'aluno':
        flash('❌ Você precisa estar logado como aluno para confirmar presença.', 'error')
        return redirect(url_for('login'))

    qr_code_lido = request.form.get('qr_code_lido')
    aluno_id = session['user_id']

    evento = Evento.query.filter_by(qr_code_link=qr_code_lido).first()

    if not evento:
        flash('❌ Código QR inválido ou evento não encontrado.', 'error')
        return redirect(url_for('meus_eventos'))

    # Verifica se o aluno está inscrito no evento
    inscricao = Inscricao.query.filter_by(aluno_id=aluno_id, evento_id=evento.id).first()

    if not inscricao:
        flash(f'❌ Você não está inscrito no evento "{evento.nome_evento}". Por favor, inscreva-se primeiro.', 'error')
        return redirect(url_for('aluno_eventos_disponiveis'))

    if inscricao.status_presenca == 'Presente':
        flash('⚠️ Presença já confirmada anteriormente.', 'warning')
        return redirect(url_for('meus_eventos'))

    agora = datetime.now()
    inicio_evento = evento.data_hora
    fim_evento = evento.data_hora + timedelta(hours=evento.duracao_horas)

    # Janela: 30 minutos antes do início até 30 minutos após o fim
    janela_inicio = inicio_evento - timedelta(minutes=30)
    janela_fim = fim_evento + timedelta(minutes=30)

    if not (janela_inicio <= agora <= janela_fim):
        flash(f'❌ Não é possível confirmar presença. O evento "{evento.nome_evento}" não está ativo no momento (data/hora: {evento.data_hora.strftime("%d/%m/%Y %H:%M")}).', 'error')
        return redirect(url_for('meus_eventos'))

    inscricao.status_presenca = 'Presente'
    db.session.commit()

    flash('✅ Presença confirmada com sucesso!', 'success')
    return redirect(url_for('meus_eventos'))


# --- Execução ---
if __name__ == '__main__':
    # criar tabelas automaticamente no início (apenas se necessário)
    with app.app_context():
        db.create_all()

    app.run(debug=True)
