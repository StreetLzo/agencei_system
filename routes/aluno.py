"""
Blueprint: Aluno
Inscrições, eventos e confirmação de presença
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import current_user
from extensions import db
from models.evento import Evento
from models.inscricao import Inscricao
from models.sala import Sala
from utils.decorators import role_required
from datetime import datetime

aluno_bp = Blueprint('aluno', __name__)


@aluno_bp.route('/eventos-disponiveis')
@role_required('aluno')
def eventos_disponiveis():
    """
    Listar eventos disponíveis para inscrição
    """
    eventos = Evento.listar_disponiveis(apenas_futuros=True)

    eventos_data = []

    for evento in eventos:
        inscrito = Inscricao.aluno_ja_inscrito(current_user.id, evento.id)
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

    # Corrigido o caminho do template
    return render_template('aluno/eventos_disponiveis.html', eventos_data=eventos_data)


@aluno_bp.route('/eventos/<int:evento_id>')
@role_required('aluno')
def detalhes_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)

    # inscrição do aluno (se existir)
    inscricao = Inscricao.query.filter_by(
        evento_id=evento.id,
        aluno_id=current_user.id
    ).first()

    # capacidade da sala
    capacidade = evento.sala.capacidade

    # total de inscritos
    total_inscritos = Inscricao.query.filter_by(evento_id=evento.id).count()

    # vagas disponíveis
    vagas_disponiveis = max(capacidade - total_inscritos, 0)

    # percentual de ocupação
    percentual = 0
    if capacidade > 0:
        percentual = int((total_inscritos / capacidade) * 100)

    return render_template(
        'aluno/detalhes_evento.html',
        evento=evento,
        inscricao=inscricao,
        capacidade=capacidade,
        total_inscritos=total_inscritos,
        vagas_disponiveis=vagas_disponiveis,
        percentual=percentual
    )



@aluno_bp.route('/eventos/<int:evento_id>/inscrever')
@role_required('aluno')
def inscrever_evento(evento_id):
    if not current_user.is_authenticated:
        flash('⚠️ Você precisa estar logado para se inscrever.', 'warning')
        session['next_url'] = url_for('aluno.confirmar_inscricao', evento_id=evento_id)
        return redirect(url_for('auth.login'))

    if not current_user.is_aluno():
        flash('❌ Apenas alunos podem se inscrever em eventos.', 'error')
        return redirect(url_for('auth.login'))

    return redirect(url_for('aluno.confirmar_inscricao', evento_id=evento_id))


@aluno_bp.route('/eventos/<int:evento_id>/confirmar-inscricao')
@role_required('aluno')
def confirmar_inscricao(evento_id):
    evento = Evento.query.get_or_404(evento_id)

    if evento.ja_iniciou():
        flash('❌ Não é possível se inscrever em eventos que já começaram.', 'error')
        return redirect(url_for('aluno.eventos_disponiveis'))

    if Inscricao.aluno_ja_inscrito(current_user.id, evento_id):
        flash('⚠️ Você já está inscrito neste evento.', 'warning')
        return redirect(url_for('aluno.meus_eventos'))

    if evento.sala and evento.num_inscritos >= evento.sala.capacidade:
        flash('❌ Não há vagas disponíveis neste evento.', 'error')
        return redirect(url_for('aluno.eventos_disponiveis'))

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


@aluno_bp.route('/meus-eventos')
@role_required('aluno')
def meus_eventos():
    filtro = request.args.get('filtro', 'todos')
    inscricoes = Inscricao.query.filter_by(aluno_id=current_user.id).all()
    eventos_data = []

    for inscricao in inscricoes:
        evento = inscricao.evento
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

    eventos_data.sort(key=lambda x: x['evento'].data_hora, reverse=True)

    return render_template(
        'aluno/meus_eventos.html',
        eventos_data=eventos_data,
        filtro=filtro
    )


@aluno_bp.route('/meus-eventos/<int:evento_id>/cancelar', methods=['POST'])
@role_required('aluno')
def cancelar_inscricao(evento_id):
    inscricao = Inscricao.query.filter_by(aluno_id=current_user.id, evento_id=evento_id).first_or_404()
    evento = inscricao.evento

    if inscricao.esta_presente:
        flash('❌ Não é possível cancelar após confirmar presença.', 'error')
        return redirect(url_for('aluno.meus_eventos'))

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


@aluno_bp.route('/escanear-qr')
@role_required('aluno')
def escanear_qr():
    return render_template('aluno/escanear_qr.html')


@aluno_bp.route('/confirmar-presenca', methods=['POST'])
@role_required('aluno')
def confirmar_presenca():
    qr_code_lido = request.form.get('qr_code_lido', '').strip()

    if not qr_code_lido:
        flash('❌ Código QR inválido.', 'error')
        return redirect(url_for('aluno.meus_eventos'))

    evento = Evento.query.filter_by(qr_code_link=qr_code_lido).first()

    if not evento:
        flash('❌ Código QR inválido ou evento não encontrado.', 'error')
        return redirect(url_for('aluno.meus_eventos'))

    inscricao = Inscricao.query.filter_by(aluno_id=current_user.id, evento_id=evento.id).first()

    if not inscricao:
        flash(f'❌ Você não está inscrito no evento "{evento.nome_evento}". Inscreva-se primeiro.', 'error')
        return redirect(url_for('aluno.eventos_disponiveis'))

    if inscricao.esta_presente:
        flash('⚠️ Presença já confirmada anteriormente.', 'warning')
        return redirect(url_for('aluno.meus_eventos'))

    if not evento.pode_confirmar_presenca():
        flash(f'❌ Não é possível confirmar presença. O evento "{evento.nome_evento}" não está na janela de confirmação (30 min antes até 30 min depois).', 'error')
        return redirect(url_for('aluno.meus_eventos'))

    try:
        inscricao.confirmar_presenca()
        flash(f'✅ Presença confirmada com sucesso no evento "{evento.nome_evento}"!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erro ao confirmar presença: {str(e)}', 'error')

    return redirect(url_for('aluno.meus_eventos'))


@aluno_bp.route('/validar-qr', methods=['POST'])
@role_required('aluno')
def validar_qr():
    qr_code = request.json.get('qr_code', '').strip()

    if not qr_code:
        return {'valido': False, 'mensagem': 'Código QR vazio'}

    evento = Evento.query.filter_by(qr_code_link=qr_code).first()

    if not evento:
        return {'valido': False, 'mensagem': 'Código QR inválido'}

    inscricao = Inscricao.query.filter_by(aluno_id=current_user.id, evento_id=evento.id).first()

    if not inscricao:
        return {'valido': False, 'mensagem': f'Você não está inscrito no evento "{evento.nome_evento}"'}

    if inscricao.esta_presente:
        return {'valido': False, 'mensagem': 'Presença já confirmada anteriormente'}

    if not evento.pode_confirmar_presenca():
        return {'valido': False, 'mensagem': 'Fora da janela de confirmação (30 min antes até 30 min depois)'}

    return {
        'valido': True,
        'evento': {
            'nome': evento.nome_evento,
            'data_hora': evento.data_hora.strftime('%d/%m/%Y às %H:%M'),
            'sala': evento.sala.nome if evento.sala else 'Não definida'
        }
    }
