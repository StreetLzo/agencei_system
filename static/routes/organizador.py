"""
Blueprint: Organizador
Gerenciamento de salas e eventos criados pelo organizador
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from datetime import datetime, timedelta

from extensions import db
from models.sala import Sala
from models.evento import Evento
from models.inscricao import Inscricao
from utils.decorators import role_required

organizador_bp = Blueprint('organizador', __name__)


@organizador_bp.route('/salas', endpoint='salas')
@role_required('organizador')
def salas():
    """Listar salas ativas"""
    salas = Sala.query.filter_by(ativa=True).order_by(Sala.capacidade.desc()).all()
    return render_template('organizador/salas.html', salas=salas)



@organizador_bp.route('/salas/<int:sala_id>/detalhes', endpoint='detalhes_sala')
@role_required('organizador')
def detalhes_sala(sala_id):
    """Detalhes da sala e eventos futuros"""
    sala = Sala.query.get_or_404(sala_id)

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
@role_required('organizador', fallback_endpoint='auth.login')
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
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Erro ao criar evento: {str(e)}', 'error')
            return render_template('organizador/reservar_sala.html', sala=sala)
    
    # GET - mostrar formulário
    return render_template('organizador/reservar_sala.html', sala=sala)


@organizador_bp.route('/reservas', endpoint='reservas')
@role_required('organizador')
def minhas_reservas():
    filtro = request.args.get('filtro', 'todos')
    query = Evento.query.filter_by(organizador_id=current_user.id)

    agora = datetime.now()

    if filtro == 'futuros':
        query = query.filter(Evento.data_hora >= agora)
    elif filtro == 'passados':
        query = query.filter(Evento.data_hora < agora)
    elif filtro == 'ativos':
        eventos = []
        for ev in query.all():
            fim = ev.data_hora + timedelta(hours=ev.duracao_horas)
            if ev.data_hora <= agora <= fim:
                eventos.append(ev)
        query = eventos
    else:
        query = query.order_by(Evento.data_hora.desc()).all()

    eventos = query if isinstance(query, list) else query.all()

    return render_template(
        'organizador/minhas_reservas.html',
        eventos=eventos,
        filtro=filtro
    )



@organizador_bp.route('/reservas/<int:evento_id>', endpoint='detalhes_evento')
@role_required('organizador')
def detalhes_evento(evento_id):
    evento = Evento.query.filter_by(
        id=evento_id,
        organizador_id=current_user.id
    ).first_or_404()

    inscricoes = Inscricao.query.filter_by(evento_id=evento.id).all()

    return render_template(
        'organizador/detalhes_evento.html',
        evento=evento,
        sala=evento.sala,
        inscricoes=inscricoes
    )


@organizador_bp.route('/reservas/<int:evento_id>/participantes')
@role_required('organizador', fallback_endpoint='auth.login')
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


@organizador_bp.route('/reservas/<int:evento_id>/editar', methods=['GET', 'POST'], endpoint='editar_evento')
@role_required('organizador')
def editar_evento(evento_id):
    evento = Evento.query.filter_by(
        id=evento_id,
        organizador_id=current_user.id
    ).first_or_404()

    if evento.ja_terminou():
        flash('❌ Evento já encerrado.', 'error')
        return redirect(url_for('organizador.reservas'))

    if request.method == 'POST':
        evento.nome_evento = request.form['nome_evento']
        evento.descricao = request.form.get('descricao') or None

        try:
            data_hora = datetime.strptime(
                f"{request.form['data']} {request.form['hora']}",
                '%Y-%m-%d %H:%M'
            )
            duracao = float(request.form['duracao'])
        except Exception:
            flash('❌ Dados inválidos.', 'error')
            return render_template('organizador/editar_evento.html', evento=evento)

        evento.data_hora = data_hora
        evento.duracao_horas = duracao

        try:
            db.session.commit()
            flash('✅ Evento atualizado!', 'success')
            return redirect(url_for('organizador.detalhes_evento', evento_id=evento.id))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Erro: {e}', 'error')

    return render_template('organizador/editar_evento.html', evento=evento)


@organizador_bp.route('/reservas/<int:evento_id>/excluir', methods=['POST'])
@role_required('organizador', fallback_endpoint='auth.login')
def excluir_evento(evento_id):
    """
    Excluir evento
    """
    evento = Evento.query.get_or_404(evento_id)
    
    # Verificar permissão
    if evento.organizador_id != current_user.id:
        flash('❌ Você não tem permissão para excluir este evento.', 'error')
        return redirect(url_for('organizador.minhas_reservas'))
    
    # Verificar se pode excluir
    if not evento.pode_ser_excluido():
        flash('❌ Não é possível excluir eventos que já ocorreram.', 'error')
        return redirect(url_for('organizador.minhas_reservas'))
    
    nome_evento = evento.nome_evento
    
    try:
        db.session.delete(evento)
        db.session.commit()
        flash(f'✅ Evento "{nome_evento}" excluído com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erro ao excluir evento: {str(e)}', 'error')
    
    return redirect(url_for('organizador.minhas_reservas'))


@organizador_bp.route('/reservas/<int:evento_id>/link-inscricao')
@role_required('organizador', fallback_endpoint='auth.login')
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