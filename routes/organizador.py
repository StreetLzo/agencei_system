"""
Blueprint: Organizador
Gerenciamento de eventos e salas por organizadores
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user
from extensions import db, csrf
from models.sala import Sala
from models.evento import Evento
from models.inscricao import Inscricao
from models.user import Usuario
from utils.decorators import role_required
from datetime import datetime, timedelta

organizador_bp = Blueprint('organizador', __name__)


@organizador_bp.route('/salas')
@role_required('organizador')
def salas():
    """
    Visualizar todas as salas disponíveis
    """
    # Buscar apenas salas ativas
    salas = Sala.query.filter_by(ativa=True).order_by(Sala.capacidade.desc()).all()
    
    return render_template('organizador/salas.html', salas=salas)


@organizador_bp.route('/salas/<int:sala_id>/detalhes')
@role_required('organizador')
def detalhes_sala(sala_id):
    """
    Ver detalhes e disponibilidade de uma sala
    """
    sala = Sala.query.get_or_404(sala_id)
    
    # Buscar eventos futuros da sala
    eventos_sala = Evento.query.filter(
        Evento.sala_id == sala_id,
        Evento.data_hora >= datetime.now()
    ).order_by(Evento.data_hora.asc()).all()
    
    return render_template(
        'organizador/detalhes_sala.html',
        sala=sala,
        eventos_sala=eventos_sala
    )


@organizador_bp.route('/salas/<int:sala_id>/reservar', methods=['GET', 'POST'])
@role_required('organizador')
def reservar_sala(sala_id):
    """
    Criar novo evento/reserva em uma sala
    """
    sala = Sala.query.get_or_404(sala_id)
    
    if not sala.ativa:
        flash('❌ Esta sala está desativada.', 'error')
        return redirect(url_for('organizador.salas'))
    
    if request.method == 'POST':
        nome_evento = request.form.get('nome_evento', '').strip()
        descricao = request.form.get('descricao', '').strip()
        data_str = request.form.get('data', '').strip()
        hora_str = request.form.get('hora', '').strip()
        duracao_str = request.form.get('duracao', '').strip()
        
        # Validações básicas
        if not all([nome_evento, data_str, hora_str, duracao_str]):
            flash('❌ Preencha todos os campos obrigatórios.', 'error')
            return render_template('organizador/reservar_sala.html', sala=sala)
        
        # Converter duração
        try:
            duracao = float(duracao_str)
            if duracao <= 0 or duracao > 12:
                flash('❌ Duração deve ser entre 0.5 e 12 horas.', 'error')
                return render_template('organizador/reservar_sala.html', sala=sala)
        except ValueError:
            flash('❌ Duração inválida.', 'error')
            return render_template('organizador/reservar_sala.html', sala=sala)
        
        # Montar data/hora
        data_hora_str = f"{data_str} {hora_str}"
        try:
            data_hora = datetime.strptime(data_hora_str, '%Y-%m-%d %H:%M')
        except ValueError:
            flash('❌ Data ou hora inválida. Use o formato correto.', 'error')
            return render_template('organizador/reservar_sala.html', sala=sala)
        
        # Validar data futura
        if data_hora < datetime.now():
            flash('❌ Não é possível criar eventos no passado.', 'error')
            return render_template('organizador/reservar_sala.html', sala=sala)
        
        # Verificar disponibilidade da sala
        disponivel, evento_conflitante = sala.esta_disponivel_em(data_hora, duracao)
        
        if not disponivel:
            flash(
                f'❌ Conflito de horário! A sala já está reservada para o evento '
                f'"{evento_conflitante.nome_evento}" em {evento_conflitante.data_hora.strftime("%d/%m/%Y às %H:%M")}.',
                'error'
            )
            return render_template('organizador/reservar_sala.html', sala=sala)
        
        # Gerar QR Code único
        qr_code_link = Evento.gerar_qr_code(
            nome_evento=nome_evento,
            data_hora=data_hora,
            sala_id=sala_id,
            organizador_id=current_user.id
        )
        
        # Criar evento
        novo_evento = Evento(
            nome_evento=nome_evento,
            descricao=descricao if descricao else None,
            data_hora=data_hora,
            duracao_horas=duracao,
            sala_id=sala_id,
            organizador_id=current_user.id,
            qr_code_link=qr_code_link
        )
        
        try:
            db.session.add(novo_evento)
            db.session.commit()
            
            flash(f'✅ Evento "{nome_evento}" criado com sucesso!', 'success')
            return redirect(url_for('organizador.minhas_reservas'))
            
        except Exception:
            db.session.rollback()
            flash('❌ Erro ao criar evento.', 'error')
            return render_template('organizador/reservar_sala.html', sala=sala)
    
    # GET - mostrar formulário
    return render_template('organizador/reservar_sala.html', sala=sala)


@organizador_bp.route('/reservas')
@role_required('organizador')
def minhas_reservas():
    """
    Listar todos os eventos criados pelo organizador
    """
    # Filtros
    filtro = request.args.get('filtro', 'todos')
    
    query = Evento.query.filter_by(organizador_id=current_user.id)
    
    if filtro == 'futuros':
        query = query.filter(Evento.data_hora >= datetime.now())
    elif filtro == 'passados':
        query = query.filter(Evento.data_hora < datetime.now())
    elif filtro == 'ativos':
        # Eventos acontecendo agora
        agora = datetime.now()
        query = query.filter(
            Evento.data_hora <= agora,
            Evento.data_hora + db.func.julianday(Evento.duracao_horas / 24.0) >= agora
        )
    
    eventos = query.order_by(Evento.data_hora.desc()).all()
    
    # Preparar dados para o template
    eventos_data = []
    for evento in eventos:
        eventos_data.append({
            'evento': evento,
            'sala': evento.sala,
            'num_inscritos': evento.num_inscritos,
            'num_presentes': evento.num_presentes,
            'pode_excluir': evento.pode_ser_excluido(),
            'ja_terminou': evento.ja_terminou(),
            'esta_ativo': evento.esta_ativo()
        })
    
    return render_template(
        'organizador/minhas_reservas.html',
        eventos_data=eventos_data,
        filtro=filtro
    )


@organizador_bp.route('/reservas/<int:evento_id>')
@role_required('organizador')
def detalhes_evento(evento_id):
    """
    Ver detalhes de um evento específico
    """
    evento = Evento.query.get_or_404(evento_id)
    
    # Verificar se o evento pertence ao organizador atual
    if evento.organizador_id != current_user.id:
        flash('❌ Você não tem permissão para ver este evento.', 'error')
        return redirect(url_for('organizador.minhas_reservas'))
    
    # Buscar inscrições
    inscricoes = Inscricao.query.filter_by(evento_id=evento_id).all()
    
    # Preparar dados dos participantes
    participantes_data = []
    for inscricao in inscricoes:
        participantes_data.append({
            'aluno': inscricao.aluno,
            'status': inscricao.status_presenca,
            'inscrito_em': inscricao.inscrito_em,
            'presenca_confirmada_em': inscricao.presenca_confirmada_em
        })
    
    return render_template(
        'organizador/detalhes_evento.html',
        evento=evento,
        sala=evento.sala,
        participantes=participantes_data
    )


@organizador_bp.route('/reservas/<int:evento_id>/participantes')
@role_required('organizador')
def lista_participantes(evento_id):
    """
    Listar participantes de um evento com QR Code
    """
    evento = Evento.query.get_or_404(evento_id)
    
    # Verificar permissão
    if evento.organizador_id != current_user.id:
        flash('❌ Você não tem permissão para acessar este evento.', 'error')
        return redirect(url_for('organizador.minhas_reservas'))
    
    # Buscar inscrições
    inscricoes = Inscricao.query.filter_by(evento_id=evento_id).all()
    
    # Preparar dados
    participantes_data = []
    for inscricao in inscricoes:
        participantes_data.append({
            'nome': inscricao.aluno.nome,
            'cpf': inscricao.aluno.cpf,
            'status': inscricao.status_presenca,
            'inscrito_em': inscricao.inscrito_em.strftime('%d/%m/%Y %H:%M'),
            'presenca_confirmada': inscricao.presenca_confirmada_em.strftime('%d/%m/%Y %H:%M') if inscricao.presenca_confirmada_em else '—'
        })
    
    return render_template(
        'organizador/lista_participantes.html',
        evento=evento,
        participantes=participantes_data,
        qr_code_value=evento.qr_code_link
    )


@organizador_bp.route('/reservas/<int:evento_id>/editar', methods=['GET', 'POST'])
@role_required('organizador')
def editar_evento(evento_id):
    """
    Editar evento existente
    """
    evento = Evento.query.get_or_404(evento_id)

    # ⬇️ AQUI (logo após buscar o evento)
    salas = Sala.query.filter_by(ativa=True).all()

    # Verificar permissão
    if evento.organizador_id != current_user.id:
        flash('❌ Você não tem permissão para editar este evento.', 'error')
        return redirect(url_for('organizador.minhas_reservas'))

    # Não permitir editar eventos passados
    if evento.ja_terminou():
        flash('❌ Não é possível editar eventos que já ocorreram.', 'error')
        return redirect(url_for('organizador.minhas_reservas'))

    if request.method == 'POST':
        nome_evento = request.form.get('nome_evento', '').strip()
        descricao = request.form.get('descricao', '').strip()
        data_str = request.form.get('data', '').strip()
        hora_str = request.form.get('hora', '').strip()
        duracao_str = request.form.get('duracao', '').strip()

        # Validações
        if not all([nome_evento, data_str, hora_str, duracao_str]):
            flash('❌ Preencha todos os campos obrigatórios.', 'error')
            return render_template(
                'organizador/editar_evento.html',
                evento=evento,
                salas=salas
            )

        try:
            duracao = float(duracao_str)
            if duracao <= 0 or duracao > 12:
                flash('❌ Duração deve ser entre 0.5 e 12 horas.', 'error')
                return render_template(
                    'organizador/editar_evento.html',
                    evento=evento,
                    salas=salas
                )
        except ValueError:
            flash('❌ Duração inválida.', 'error')
            return render_template(
                'organizador/editar_evento.html',
                evento=evento,
                salas=salas
            )

        # Montar data/hora
        data_hora_str = f"{data_str} {hora_str}"
        try:
            data_hora = datetime.strptime(data_hora_str, '%Y-%m-%d %H:%M')
        except ValueError:
            flash('❌ Data ou hora inválida.', 'error')
            return render_template(
                'organizador/editar_evento.html',
                evento=evento,
                salas=salas
            )

        if data_hora < datetime.now():
            flash('❌ Não é possível agendar eventos no passado.', 'error')
            return render_template(
                'organizador/editar_evento.html',
                evento=evento,
                salas=salas
            )

        # Verificar conflito
        eventos_sala = Evento.query.filter(
            Evento.sala_id == evento.sala_id,
            Evento.id != evento.id
        ).all()

        data_fim = data_hora + timedelta(hours=duracao)

        for ev in eventos_sala:
            ev_fim = ev.data_hora + timedelta(hours=ev.duracao_horas)
            if (data_hora < ev_fim) and (ev.data_hora < data_fim):
                flash(
                    f'❌ Conflito com o evento "{ev.nome_evento}" '
                    f'em {ev.data_hora.strftime("%d/%m/%Y às %H:%M")}.',
                    'error'
                )
                return render_template(
                    'organizador/editar_evento.html',
                    evento=evento,
                    salas=salas
                )

        # Atualizar evento
        evento.nome_evento = nome_evento
        evento.descricao = descricao if descricao else None
        evento.data_hora = data_hora
        evento.duracao_horas = duracao

        try:
            db.session.commit()
            flash('✅ Evento atualizado com sucesso!', 'success')
            return redirect(
                url_for('organizador.detalhes_evento', evento_id=evento.id)
            )
        except Exception:
            db.session.rollback()
            flash('❌ Erro ao atualizar evento.', 'error')

    # GET
    return render_template(
        'organizador/editar_evento.html',
        evento=evento,
        salas=salas
    )



@organizador_bp.route('/reservas/<int:evento_id>/excluir', methods=['POST'])
@role_required('organizador')
def excluir_evento(evento_id):
    """
    Soft-delete: marca evento como cancelado em vez de apagar
    """
    evento = Evento.query.get_or_404(evento_id)
    
    if evento.organizador_id != current_user.id:
        flash('❌ Você não tem permissão para excluir este evento.', 'error')
        return redirect(url_for('organizador.minhas_reservas'))
    
    if not evento.pode_ser_excluido():
        flash('❌ Não é possível excluir eventos que já ocorreram.', 'error')
        return redirect(url_for('organizador.minhas_reservas'))
    
    nome_evento = evento.nome_evento
    
    try:
        evento.status = 'cancelado'
        db.session.commit()
        flash(f'✅ Evento "{nome_evento}" cancelado com sucesso.', 'success')
    except Exception:
        db.session.rollback()
        flash('❌ Erro ao cancelar evento.', 'error')
    
    return redirect(url_for('organizador.minhas_reservas'))


@organizador_bp.route('/reservas/<int:evento_id>/link-inscricao')
@role_required('organizador')
def gerar_link_inscricao(evento_id):
    """
    Gerar link de inscrição compartilhável
    """
    evento = Evento.query.get_or_404(evento_id)
    
    # Verificar permissão
    if evento.organizador_id != current_user.id:
        flash('❌ Você não tem permissão para acessar este evento.', 'error')
        return redirect(url_for('organizador.minhas_reservas'))
    
    # Gerar URL completo
    link_inscricao = url_for('aluno.inscrever_evento', evento_id=evento.id, _external=True)
    
    return render_template(
        'organizador/link_inscricao.html',
        evento=evento,
        link_inscricao=link_inscricao
    )

@organizador_bp.route('/reservas/<int:evento_id>/cancelar', methods=['POST'])
@role_required('organizador')
def cancelar_evento(evento_id):
    """
    Soft-delete: marca evento como cancelado (POST only)
    """
    evento = Evento.query.get_or_404(evento_id)

    if evento.organizador_id != current_user.id:
        flash('❌ Você não tem permissão para cancelar este evento.', 'error')
        return redirect(url_for('organizador.minhas_reservas'))

    if evento.ja_terminou():
        flash('❌ Não é possível cancelar eventos que já ocorreram.', 'error')
        return redirect(url_for('organizador.detalhes_evento', evento_id=evento.id))

    try:
        evento.status = 'cancelado'
        db.session.commit()
        flash('✅ Evento cancelado com sucesso.', 'success')
    except Exception:
        db.session.rollback()
        flash('❌ Erro ao cancelar evento.', 'error')

    return redirect(url_for('organizador.minhas_reservas'))


# ================================================================
#  API endpoint para QR Code Dinâmico (TOTP)
# ================================================================
@organizador_bp.route('/reservas/<int:evento_id>/totp-token', methods=['GET'])
@role_required('organizador')
@csrf.exempt
def totp_token(evento_id):
    """
    Retorna o token TOTP atual do evento em JSON.
    O frontend do organizador faz polling a cada 5s para atualizar o QR.
    """
    evento = Evento.query.get_or_404(evento_id)

    if evento.organizador_id != current_user.id:
        return jsonify({'error': 'Sem permissão'}), 403

    token, segundos_restantes = evento.gerar_token_temporal()

    return jsonify({
        'evento_id': evento.id,
        'token': token,
        'segundos_restantes': segundos_restantes,
        'qr_payload': f'{evento.id}:{token}'
    })
