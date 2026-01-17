"""
Blueprint: Admin
Dashboard e gerenciamento do sistema
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from extensions import db
from models.user import Usuario
from models.sala import Sala
from models.evento import Evento
from models.inscricao import Inscricao
from models.pre_authorized_user import PreAuthorizedUser
from utils.decorators import role_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard')
@role_required('admin')
def dashboard():
    """
    Dashboard administrativo com estatísticas
    """
    # Estatísticas gerais
    total_usuarios = Usuario.query.count()
    total_alunos = Usuario.query.filter_by(tipo='aluno').count()
    total_organizadores = Usuario.query.filter_by(tipo='organizador').count()
    total_admins = Usuario.query.filter_by(tipo='admin').count()
    
    total_salas = Sala.query.count()
    total_eventos = Evento.query.count()
    total_inscricoes = Inscricao.query.count()
    
    # CPFs pré-autorizados
    cpfs_autorizados_disponiveis = PreAuthorizedUser.query.filter_by(usado=False, ativo=True).count()
    cpfs_autorizados_total = PreAuthorizedUser.query.count()
    
    # Eventos recentes
    eventos_recentes = Evento.query.order_by(Evento.criado_em.desc()).limit(5).all()
    
    # Inscrições recentes
    inscricoes_recentes = Inscricao.query.order_by(Inscricao.inscrito_em.desc()).limit(5).all()
    
    return render_template(
        'admin/dashboard.html',
        total_usuarios=total_usuarios,
        total_alunos=total_alunos,
        total_organizadores=total_organizadores,
        total_admins=total_admins,
        total_salas=total_salas,
        total_eventos=total_eventos,
        total_inscricoes=total_inscricoes,
        cpfs_autorizados_disponiveis=cpfs_autorizados_disponiveis,
        cpfs_autorizados_total=cpfs_autorizados_total,
        eventos_recentes=eventos_recentes,
        inscricoes_recentes=inscricoes_recentes
    )


@admin_bp.route('/usuarios')
@role_required('admin')
def usuarios():
    """
    Listar todos os usuários
    """
    # Filtros
    tipo_filtro = request.args.get('tipo', 'todos')
    busca = request.args.get('busca', '').strip()
    
    query = Usuario.query
    
    # Filtro por tipo
    if tipo_filtro != 'todos':
        query = query.filter_by(tipo=tipo_filtro)
    
    # Busca por nome ou CPF
    if busca:
        query = query.filter(
            db.or_(
                Usuario.nome.ilike(f'%{busca}%'),
                Usuario.cpf.ilike(f'%{busca}%')
            )
        )
    
    usuarios = query.order_by(Usuario.criado_em.desc()).all()
    
    return render_template(
        'admin/usuarios.html',
        usuarios=usuarios,
        tipo_filtro=tipo_filtro,
        busca=busca
    )


@admin_bp.route('/usuarios/<int:user_id>/alternar-status', methods=['POST'])
@role_required('admin')
def alternar_status_usuario(user_id):
    """
    Ativar/desativar usuário
    """
    usuario = Usuario.query.get_or_404(user_id)
    
    # Não permitir desativar a si mesmo
    if usuario.id == current_user.id:
        flash('❌ Você não pode desativar sua própria conta.', 'error')
        return redirect(url_for('admin.usuarios'))
    
    # Alternar status
    usuario.ativo = not usuario.ativo
    
    try:
        db.session.commit()
        status = "ativado" if usuario.ativo else "desativado"
        flash(f'✅ Usuário {usuario.nome} foi {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erro ao alterar status: {str(e)}', 'error')
    
    return redirect(url_for('admin.usuarios'))


@admin_bp.route('/cpfs_autorizados')
@role_required('admin')
def cpfs_autorizados():
    status_filtro = request.args.get('status', 'todos')
    query = PreAuthorizedUser.query

    if status_filtro == 'disponiveis':
        query = query.filter_by(usado=False, ativo=True)
    elif status_filtro == 'usados':
        query = query.filter_by(usado=True)
    elif status_filtro == 'inativos':
        query = query.filter_by(ativo=False)

    cpfs = query.order_by(PreAuthorizedUser.criado_em.desc()).all()

    # Mudamos o nome do template e da variável enviada (autorizados)
    return render_template(
        'admin/cpfs_autorizados.html',
        autorizados=cpfs,
        status_filtro=status_filtro
    )

@admin_bp.route('/cpfs_autorizados/adicionar', methods=['POST'])
@role_required('admin')
def adicionar_cpf_autorizado():
    cpf = request.form.get('cpf', '').strip()
    # No seu HTML o campo chama 'nome', mas seu modelo parece usar apenas CPF e Role. 
    # Se o seu modelo PreAuthorizedUser tiver o campo 'nome', adicione-o aqui.
    role = request.form.get('role', 'organizador')

    cpf = ''.join(filter(str.isdigit, cpf))

    pre_auth, mensagem = PreAuthorizedUser.criar_autorizacao(
        cpf=cpf,
        role=role,
        criado_por_id=current_user.id
    )

    if pre_auth:
        flash(f'✅ {mensagem}', 'success')
    else:
        flash(f'❌ {mensagem}', 'error')

    return redirect(url_for('admin.cpfs_autorizados'))

@admin_bp.route('/cpfs_autorizados/<int:cpf_id>/desativar', methods=['POST'])
@role_required('admin')
def desativar_cpf_autorizado(cpf_id):
    pre_auth = PreAuthorizedUser.query.get_or_404(cpf_id)
    try:
        pre_auth.desativar()
        flash('✅ CPF desativado com sucesso.', 'success')
    except Exception as e:
        flash(f'❌ Erro ao desativar: {str(e)}', 'error')
    return redirect(url_for('admin.cpfs_autorizados'))

@admin_bp.route('/cpfs_autorizados/<int:cpf_id>/reativar', methods=['POST'])
@role_required('admin')
def reativar_cpf_autorizado(cpf_id):
    pre_auth = PreAuthorizedUser.query.get_or_404(cpf_id)
    try:
        pre_auth.reativar()
        flash('✅ CPF reativado com sucesso.', 'success')
    except Exception as e:
        flash(f'❌ Erro ao reativar: {str(e)}', 'error')
    return redirect(url_for('admin.cpfs_autorizados'))


@admin_bp.route('/salas')
@role_required('admin')
def salas():
    """
    Gerenciar salas
    """
    salas = Sala.query.order_by(Sala.capacidade.desc()).all()
    return render_template('admin/salas.html', salas=salas)


@admin_bp.route('/salas/adicionar', methods=['GET', 'POST'])
@role_required('admin')
def adicionar_sala():
    """
    Adicionar nova sala
    """
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        capacidade = request.form.get('capacidade', 0)
        descricao = request.form.get('descricao', '').strip()
        
        try:
            capacidade = int(capacidade)
        except ValueError:
            flash('❌ Capacidade inválida.', 'error')
            return render_template('admin/adicionar_sala.html')
        
        if not nome or capacidade <= 0:
            flash('❌ Preencha todos os campos corretamente.', 'error')
            return render_template('admin/adicionar_sala.html')
        
        # Verificar se já existe
        if Sala.query.filter_by(nome=nome).first():
            flash('❌ Já existe uma sala com este nome.', 'error')
            return render_template('admin/adicionar_sala.html')
        
        nova_sala = Sala(
            nome=nome,
            capacidade=capacidade,
            descricao=descricao if descricao else None
        )
        
        try:
            db.session.add(nova_sala)
            db.session.commit()
            flash('✅ Sala adicionada com sucesso!', 'success')
            return redirect(url_for('admin.salas'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Erro ao adicionar sala: {str(e)}', 'error')
    
    return render_template('admin/adicionar_sala.html')


@admin_bp.route('/salas/<int:sala_id>/editar', methods=['GET', 'POST'])
@role_required('admin')
def editar_sala(sala_id):
    """
    Editar sala existente
    """
    sala = Sala.query.get_or_404(sala_id)
    
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        capacidade = request.form.get('capacidade', 0)
        descricao = request.form.get('descricao', '').strip()
        
        try:
            capacidade = int(capacidade)
        except ValueError:
            flash('❌ Capacidade inválida.', 'error')
            return render_template('admin/editar_sala.html', sala=sala)
        
        if not nome or capacidade <= 0:
            flash('❌ Preencha todos os campos corretamente.', 'error')
            return render_template('admin/editar_sala.html', sala=sala)
        
        # Verificar nome duplicado (exceto a própria sala)
        sala_duplicada = Sala.query.filter(
            Sala.nome == nome,
            Sala.id != sala_id
        ).first()
        
        if sala_duplicada:
            flash('❌ Já existe outra sala com este nome.', 'error')
            return render_template('admin/editar_sala.html', sala=sala)
        
        sala.nome = nome
        sala.capacidade = capacidade
        sala.descricao = descricao if descricao else None
        
        try:
            db.session.commit()
            flash('✅ Sala atualizada com sucesso!', 'success')
            return redirect(url_for('admin.salas'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Erro ao atualizar sala: {str(e)}', 'error')
    
    return render_template('admin/editar_sala.html', sala=sala)


@admin_bp.route('/salas/<int:sala_id>/alternar-status', methods=['POST'])
@role_required('admin')
def alternar_status_sala(sala_id):
    """
    Ativar/desativar sala
    """
    sala = Sala.query.get_or_404(sala_id)
    sala.ativa = not sala.ativa
    
    try:
        db.session.commit()
        status = "ativada" if sala.ativa else "desativada"
        flash(f'✅ Sala {sala.nome} foi {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erro ao alterar status: {str(e)}', 'error')
    
    return redirect(url_for('admin.salas'))


@admin_bp.route('/eventos')
@role_required('admin')
def eventos():
    """
    Listar todos os eventos (visão geral)
    """
    eventos = Evento.query.order_by(Evento.data_hora.desc()).all()
    return render_template('admin/eventos.html', eventos=eventos)