
"""
Blueprint: Aluno
Inscrições, eventos e confirmação de presença
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import current_user, login_required
from extensions import db
from models.evento import Evento
from models.inscricao import Inscricao
from models.sala import Sala
from utils.decorators import role_required
from datetime import datetime

aluno_bp = Blueprint('aluno', __name__)


@aluno_bp.route('/eventos')
@role_required('aluno', fallback_endpoint='aluno.eventos_disponiveis')
def eventos_disponiveis():
    """
    Listar eventos disponíveis para inscrição
    """
    # Buscar apenas eventos futuros
    eventos = Evento.listar_disponiveis(apenas_futuros=True)
    
    # Preparar dados
    eventos_data = []
    for evento in eventos:
        # Verificar se já está inscrito
        inscrito = Inscricao.aluno_ja_inscrito(current_user.id, evento.id)
        
        # Verificar vagas
        tem_vagas = evento.sala.capacidade > evento.num_inscritos if evento.sala else True
        
        eventos_data.append({
            'evento': evento,
            'sala': evento.sala,
            'organizador': evento.organizador,
            'num_inscritos': evento.num_inscritos,
            'capacidade': evento.sala.capacidade if evento.sala else 0,
            'tem_vagas': tem_vagas,
            'inscrito': inscrito,
            'pode_inscrever': not inscrito and tem_vagas and not evento.ja_iniciou()
        })
    
    return render_template('aluno/eventos_disponiveis.html', eventos_data=eventos_data)


@aluno_bp.route('/eventos/<int:evento_id>/detalhes')
@role_required('aluno')
def detalhes_evento(evento_id):
    """
    Ver detalhes de um evento
    """
    evento = Evento.query.get_or_404(evento_id)
    
    # Verificar se está inscrito
    inscricao = Inscricao.query.filter_by(
        aluno_id=current_user.id,
        evento_id=evento_id
    ).first()
    
    return render_template(
        'aluno/detalhes_evento.html',
        evento=evento,
        sala=evento.sala,
        organizador=evento.organizador,
        inscricao=inscricao
    )


@aluno_bp.route('/eventos/<int:evento_id>/inscrever')
@role_required('aluno')
def inscrever_evento(evento_id):
    """
    Rota de inscrição em evento (acessível por link)
    Se não estiver logado, salva o destino e redireciona para login
    """
    if not current_user.is_authenticated:
        flash('⚠️ Você precisa estar logado para se inscrever.', 'warning')
        # Salvar URL de destino
        session['next_url'] = url_for('aluno.confirmar_inscricao', evento_id=evento_id)
        return redirect(url_for('auth.login'))
    
    # Se não for aluno, bloquear
    if not current_user.is_aluno():
        flash('❌ Apenas alunos podem se inscrever em eventos.', 'error')
        return redirect(url_for('auth.login'))
    
    # Redirecionar para confirmação
    return redirect(url_for('aluno.confirmar_inscricao', evento_id=evento_id))


@aluno_bp.route('/eventos/<int:evento_id>/confirmar-inscricao')
@role_required('aluno')
def confirmar_inscricao(evento_id):
    """
    Confirmar inscrição em evento
    """
    evento = Evento.query.get_or_404(evento_id)
    
    # Verificar se evento já passou
    if evento.ja_iniciou():
        flash('❌ Não é possível se inscrever em eventos que já começaram.', 'error')
        return redirect(url_for('aluno.eventos_disponiveis'))
    
    # Verificar se já está inscrito
    if Inscricao.aluno_ja_inscrito(current_user.id, evento_id):
        flash('⚠️ Você já está inscrito neste evento.', 'warning')
        return redirect(url_for('aluno.meus_eventos'))
    
    # Verificar capacidade da sala
    if evento.sala:
        if evento.num_inscritos >= evento.sala.capacidade:
            flash('❌ Não há vagas disponíveis neste evento.', 'error')
            return redirect(url_for('aluno.eventos_disponiveis'))
    
    # Criar inscrição
    nova_inscricao = Inscricao(
        aluno_id=current_user.id,
        evento_id=evento_id,
        status_presenca=Inscricao.STATUS_AGUARDANDO
    )
    
    try:
        db.session.add(nova_inscricao)
        db.session.commit()
        
        flash(f'✅ Inscrição realizada com sucesso no evento "{evento.nome_evento}"!', 'success')
        return redirect(url_for('aluno.meus_eventos'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erro ao realizar inscrição: {str(e)}', 'error')
        return redirect(url_for('aluno.eventos_disponiveis'))


@aluno_bp.route('/meus_eventos ')
@role_required('aluno')
def meus_eventos():
    """
    Listar eventos em que o aluno está inscrito
    """
    # Filtro
    filtro = request.args.get('filtro', 'todos')
    
    # Buscar inscrições do aluno
    inscricoes = Inscricao.query.filter_by(aluno_id=current_user.id).all()
    
    # Preparar dados
    eventos_data = []
    for inscricao in inscricoes:
        evento = inscricao.evento
        
        # Aplicar filtro
        if filtro == 'futuros' and evento.ja_iniciou():
            continue
        elif filtro == 'passados' and not evento.ja_terminou():
            continue
        elif filtro == 'ativos' and not evento.esta_ativo():
            continue
        
        eventos_data.append({
            'evento': evento,
            'sala': evento.sala,
            'inscricao': inscricao,
            'pode_confirmar': evento.pode_confirmar_presenca(),
            'ja_confirmou': inscricao.esta_presente
        })
    
    # Ordenar por data
    eventos_data.sort(key=lambda x: x['evento'].data_hora, reverse=True)
    
    return render_template(
        'aluno/meus_eventos.html',
        eventos_data=eventos_data,
        filtro=filtro
    )


@aluno_bp.route('/meus_eventos/<int:evento_id>/cancelar', methods=['POST'])
@role_required('aluno')
def cancelar_inscricao(evento_id):
    """
    Cancelar inscrição em evento
    """
    inscricao = Inscricao.query.filter_by(
        aluno_id=current_user.id,
        evento_id=evento_id
    ).first_or_404()
    
    evento = inscricao.evento
    
    # Não permitir cancelar se já confirmou presença
    if inscricao.esta_presente:
        flash('❌ Não é possível cancelar após confirmar presença.', 'error')
        return redirect(url_for('aluno.meus_eventos'))
    
    # Não permitir cancelar eventos passados
    if evento.ja_terminou():
        flash('❌ Não é possível cancelar inscrição em eventos passados.', 'error')
        return redirect(url_for('aluno.meus_eventos'))
    
    nome_evento = evento.nome_evento
    
    try:
        db.session.delete(inscricao)
        db.session.commit()
        flash(f'✅ Inscrição cancelada no evento "{nome_evento}".', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erro ao cancelar inscrição: {str(e)}', 'error')
    
    return redirect(url_for('aluno.meus_eventos'))


@aluno_bp.route('/escanear_qr')
@role_required('aluno')
def escanear_qr():
    """
    Interface para escanear QR Code e confirmar presença
    """
    return render_template('aluno/escanear_qr.html')


@aluno_bp.route('/confirmar_presenca', methods=['POST'])
@role_required('aluno')
def confirmar_presenca():
    """
    Confirmar presença via QR Code
    """
    qr_code_lido = request.form.get('qr_code_lido', '').strip()
    
    if not qr_code_lido:
        flash('❌ Código QR inválido.', 'error')
        return redirect(url_for('aluno.meus_eventos'))
    
    # Buscar evento pelo QR Code
    evento = Evento.query.filter_by(qr_code_link=qr_code_lido).first()
    
    if not evento:
        flash('❌ Código QR inválido ou evento não encontrado.', 'error')
        return redirect(url_for('aluno.meus_eventos'))
    
    # Verificar se está inscrito
    inscricao = Inscricao.query.filter_by(
        aluno_id=current_user.id,
        evento_id=evento.id
    ).first()
    
    if not inscricao:
        flash(
            f'❌ Você não está inscrito no evento "{evento.nome_evento}". '
            f'Inscreva-se primeiro.',
            'error'
        )
        return redirect(url_for('aluno.eventos_disponiveis'))
    
    # Verificar se já confirmou
    if inscricao.esta_presente:
        flash('⚠️ Presença já confirmada anteriormente.', 'warning')
        return redirect(url_for('aluno.meus_eventos'))
    
    # Verificar janela de confirmação
    if not evento.pode_confirmar_presenca():
        flash(
            f'❌ Não é possível confirmar presença. O evento "{evento.nome_evento}" '
            f'não está na janela de confirmação (30 min antes até 30 min depois).',
            'error'
        )
        return redirect(url_for('aluno.meus_eventos'))
    
    # Confirmar presença
    try:
        inscricao.confirmar_presenca()
        flash(
            f'✅ Presença confirmada com sucesso no evento "{evento.nome_evento}"!',
            'success'
        )
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erro ao confirmar presença: {str(e)}', 'error')
    
    return redirect(url_for('aluno.meus_eventos'))


@aluno_bp.route('/validar_qr', methods=['POST'])
@role_required('aluno')
def validar_qr():
    """
    Endpoint AJAX para validar QR Code antes da confirmação
    Retorna informações do evento
    """
    qr_code = request.json.get('qr_code', '').strip()
    
    if not qr_code:
        return {'valido': False, 'mensagem': 'Código QR vazio'}
    
    # Buscar evento
    evento = Evento.query.filter_by(qr_code_link=qr_code).first()
    
    if not evento:
        return {'valido': False, 'mensagem': 'Código QR inválido'}
    
    # Verificar inscrição
    inscricao = Inscricao.query.filter_by(
        aluno_id=current_user.id,
        evento_id=evento.id
    ).first()
    
    if not inscricao:
        return {
            'valido': False,
            'mensagem': f'Você não está inscrito no evento "{evento.nome_evento}"'
        }
    
    # Verificar se já confirmou
    if inscricao.esta_presente:
        return {
            'valido': False,
            'mensagem': 'Presença já confirmada anteriormente'
        }
    
    # Verificar janela
    if not evento.pode_confirmar_presenca():
        return {
            'valido': False,
            'mensagem': 'Fora da janela de confirmação (30 min antes até 30 min depois)'
        }
    
    # Tudo OK
    return {
        'valido': True,
        'evento': {
            'nome': evento.nome_evento,
            'data_hora': evento.data_hora.strftime('%d/%m/%Y às %H:%M'),
            'sala': evento.sala.nome if evento.sala else 'Não definida'
        }
    }