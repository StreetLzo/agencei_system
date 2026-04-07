"""
Blueprint: Autenticação
Gerencia login, logout e cadastro de usuários
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, current_user
from extensions import db, limiter, csrf
from models.user import Usuario
from models.pre_authorized_user import PreAuthorizedUser
from utils.decorators import role_required, login_required_custom, anonymous_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
@anonymous_required()
@limiter.limit('5 per minute', methods=['POST'])
def login():
    """
    Página de login
    Aceita aluno, organizador e admin
    """
    if request.method == 'POST':
        cpf = request.form.get('cpf', '').strip()
        senha = request.form.get('senha', '').strip()
        lembrar = request.form.get('lembrar', False)
        
        if not cpf or not senha:
            flash('❌ Por favor, preencha todos os campos.', 'error')
            return render_template('auth/login.html')
        
        cpf = ''.join(filter(str.isdigit, cpf))
        usuario = Usuario.query.filter_by(cpf=cpf).first()
        
        if not usuario:
            flash('❌ CPF não encontrado.', 'error')
            return render_template('auth/login.html')
        
        if not usuario.check_password(senha):
            flash('❌ Senha incorreta.', 'error')
            return render_template('auth/login.html')
        
        if not usuario.ativo:
            flash('❌ Usuário desativado. Contate o administrador.', 'error')
            return render_template('auth/login.html')
        
        login_user(usuario, remember=lembrar)
        flash(f'✅ Bem-vindo(a), {usuario.nome}!', 'success')
        
        next_url = session.pop('next_url', None)
        if next_url:
            return redirect(next_url)
        
        # Redireciona baseado no tipo de usuário
        if usuario.is_admin():
            return redirect(url_for('admin.dashboard'))
        elif usuario.is_organizador():
            return redirect(url_for('organizador.salas'))
        elif usuario.is_aluno():
            return redirect(url_for('aluno.eventos_disponiveis'))
        
        return redirect(url_for('auth.login'))
    
    if 'next_url' in request.args:
        session['next_url'] = request.args['next_url']
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    """
    Logout do usuário
    """
    logout_user()
    session.pop('next_url', None)
    flash('👋 Você saiu da sua conta.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/cadastro', methods=['GET', 'POST'])
@anonymous_required()
def cadastro():
    """
    Cadastro de ALUNOS (livre)
    Organizadores devem ser criados pelo admin
    """
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        cpf = request.form.get('cpf', '').strip()
        senha = request.form.get('senha', '').strip()
        confirmar_senha = request.form.get('confirmar_senha', '').strip()
        
        if not all([nome, cpf, senha, confirmar_senha]):
            flash('❌ Por favor, preencha todos os campos.', 'error')
            return render_template('auth/cadastro.html')
        
        cpf = ''.join(filter(str.isdigit, cpf))
        
        if not Usuario.validar_cpf(cpf):
            flash('❌ CPF inválido.', 'error')
            return render_template('auth/cadastro.html')
        
        if Usuario.query.filter_by(cpf=cpf).first():
            flash('❌ CPF já cadastrado no sistema.', 'error')
            return render_template('auth/cadastro.html')
        
        if senha != confirmar_senha:
            flash('❌ As senhas não coincidem.', 'error')
            return render_template('auth/cadastro.html')
        
        if len(senha) < 6:
            flash('❌ A senha deve ter no mínimo 6 caracteres.', 'error')
            return render_template('auth/cadastro.html')
        
        novo_usuario = Usuario(
            nome=nome,
            cpf=cpf,
            tipo='aluno'
        )
        novo_usuario.set_password(senha)
        
        try:
            db.session.add(novo_usuario)
            db.session.commit()
            flash('✅ Cadastro realizado com sucesso! Faça login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception:
            db.session.rollback()
            flash('❌ Erro ao criar conta. Tente novamente.', 'error')
            return render_template('auth/cadastro.html')
    
    return render_template('auth/cadastro.html')


@auth_bp.route('/cadastro/organizador', methods=['GET', 'POST'])
@anonymous_required()
def cadastro_organizador():
    """
    Cadastro de ORGANIZADORES (requer CPF pré-autorizado)
    """
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        cpf = request.form.get('cpf', '').strip()
        senha = request.form.get('senha', '').strip()
        confirmar_senha = request.form.get('confirmar_senha', '').strip()
        
        if not all([nome, cpf, senha, confirmar_senha]):
            flash('❌ Por favor, preencha todos os campos.', 'error')
            return render_template('auth/cadastro_organizador.html')
        
        cpf = ''.join(filter(str.isdigit, cpf))
        
        if not Usuario.validar_cpf(cpf):
            flash('❌ CPF inválido.', 'error')
            return render_template('auth/cadastro_organizador.html')
        
        pre_auth = PreAuthorizedUser.cpf_autorizado(cpf, role='organizador')
        if not pre_auth:
            flash('❌ CPF não autorizado para cadastro como organizador. Contate o administrador.', 'error')
            return render_template('auth/cadastro_organizador.html')
        
        if Usuario.query.filter_by(cpf=cpf).first():
            flash('❌ CPF já cadastrado no sistema.', 'error')
            return render_template('auth/cadastro_organizador.html')
        
        if senha != confirmar_senha:
            flash('❌ As senhas não coincidem.', 'error')
            return render_template('auth/cadastro_organizador.html')
        
        if len(senha) < 6:
            flash('❌ A senha deve ter no mínimo 6 caracteres.', 'error')
            return render_template('auth/cadastro_organizador.html')
        
        novo_usuario = Usuario(
            nome=nome,
            cpf=cpf,
            tipo='organizador'
        )
        novo_usuario.set_password(senha)
        
        try:
            db.session.add(novo_usuario)
            pre_auth.marcar_como_usado()
            db.session.commit()
            flash('✅ Cadastro de organizador realizado com sucesso! Faça login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception:
            db.session.rollback()
            flash('❌ Erro ao criar conta. Tente novamente.', 'error')
            return render_template('auth/cadastro_organizador.html')
    
    return render_template('auth/cadastro_organizador.html')


@auth_bp.route('/verificar-cpf-organizador', methods=['POST'])
@limiter.limit('10 per minute')
@csrf.exempt
def verificar_cpf_organizador():
    """
    Endpoint AJAX para verificar se CPF está autorizado
    """
    cpf = request.json.get('cpf', '').strip()
    cpf = ''.join(filter(str.isdigit, cpf))
    
    if not Usuario.validar_cpf(cpf):
        return {'valido': False, 'mensagem': 'CPF inválido'}
    
    pre_auth = PreAuthorizedUser.cpf_autorizado(cpf, role='organizador')
    
    if pre_auth:
        return {'valido': True, 'mensagem': 'CPF autorizado para cadastro!'}
    else:
        return {'valido': False, 'mensagem': 'CPF não autorizado. Contate o administrador.'}
