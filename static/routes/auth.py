"""
Blueprint: Autenticação
Gerencia login, logout e cadastro de usuários
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, current_user
from extensions import db
from models.user import Usuario
from models.pre_authorized_user import PreAuthorizedUser
from utils.decorators import anonymous_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
@anonymous_required
def login():
    """
    Página de login
    Aceita aluno, organizador e admin
    """
    if request.method == 'POST':
        cpf = request.form.get('cpf', '').strip()
        senha = request.form.get('senha', '').strip()
        lembrar = request.form.get('lembrar', False)
        
        # Validações básicas
        if not cpf or not senha:
            flash('❌ Por favor, preencha todos os campos.', 'error')
            return render_template('auth/login.html')
        
        # Limpar CPF (remover pontos e traços)
        cpf = ''.join(filter(str.isdigit, cpf))
        
        # Buscar usuário
        usuario = Usuario.query.filter_by(cpf=cpf).first()
        
        # Verificar credenciais
        if not usuario:
            flash('❌ CPF não encontrado.', 'error')
            return render_template('auth/login.html')
        
        if not usuario.check_password(senha):
            flash('❌ Senha incorreta.', 'error')
            return render_template('auth/login.html')
        
        if not usuario.ativo:
            flash('❌ Usuário desativado. Contate o administrador.', 'error')
            return render_template('auth/login.html')
        
        # Login bem-sucedido
        login_user(usuario, remember=lembrar)
        flash(f'✅ Bem-vindo(a), {usuario.nome}!', 'success')
        
        # Redirecionar para página salva ou página padrão do tipo
        next_url = session.pop('next_url', None)
        if next_url:
            return redirect(next_url)
        
        # Redirecionar baseado no tipo
        if usuario.is_admin():
            return redirect(url_for('admin.dashboard'))
        elif usuario.is_organizador():
            return redirect(url_for('organizador.salas'))
        elif usuario.is_aluno():
            return redirect(url_for('aluno.eventos_disponiveis'))
        
        return redirect(url_for('auth.login'))
    
    # Salvar next_url se fornecido
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
@anonymous_required
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
        
        # Validações básicas
        if not all([nome, cpf, senha, confirmar_senha]):
            flash('❌ Por favor, preencha todos os campos.', 'error')
            return render_template('auth/cadastro.html')
        
        # Limpar CPF
        cpf = ''.join(filter(str.isdigit, cpf))
        
        # Validar CPF
        if not Usuario.validar_cpf(cpf):
            flash('❌ CPF inválido.', 'error')
            return render_template('auth/cadastro.html')
        
        # Verificar se CPF já existe
        if Usuario.query.filter_by(cpf=cpf).first():
            flash('❌ CPF já cadastrado no sistema.', 'error')
            return render_template('auth/cadastro.html')
        
        # Verificar senhas
        if senha != confirmar_senha:
            flash('❌ As senhas não coincidem.', 'error')
            return render_template('auth/cadastro.html')
        
        if len(senha) < 6:
            flash('❌ A senha deve ter no mínimo 6 caracteres.', 'error')
            return render_template('auth/cadastro.html')
        
        # Criar novo usuário (sempre como ALUNO)
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
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Erro ao criar conta: {str(e)}', 'error')
            return render_template('auth/cadastro.html')
    
    return render_template('auth/cadastro.html')


@auth_bp.route('/cadastro/organizador', methods=['GET', 'POST'])
@anonymous_required
def cadastro_organizador():
    """
    Cadastro de ORGANIZADORES (requer CPF pré-autorizado)
    """
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        cpf = request.form.get('cpf', '').strip()
        senha = request.form.get('senha', '').strip()
        confirmar_senha = request.form.get('confirmar_senha', '').strip()
        
        # Validações básicas
        if not all([nome, cpf, senha, confirmar_senha]):
            flash('❌ Por favor, preencha todos os campos.', 'error')
            return render_template('auth/cadastro_organizador.html')
        
        # Limpar CPF
        cpf = ''.join(filter(str.isdigit, cpf))
        
        # Validar CPF
        if not Usuario.validar_cpf(cpf):
            flash('❌ CPF inválido.', 'error')
            return render_template('auth/cadastro_organizador.html')
        
        # VERIFICAR SE CPF ESTÁ PRÉ-AUTORIZADO
        pre_auth = PreAuthorizedUser.cpf_autorizado(cpf, role='organizador')
        if not pre_auth:
            flash('❌ CPF não autorizado para cadastro como organizador. Contate o administrador.', 'error')
            return render_template('auth/cadastro_organizador.html')
        
        # Verificar se CPF já existe
        if Usuario.query.filter_by(cpf=cpf).first():
            flash('❌ CPF já cadastrado no sistema.', 'error')
            return render_template('auth/cadastro_organizador.html')
        
        # Verificar senhas
        if senha != confirmar_senha:
            flash('❌ As senhas não coincidem.', 'error')
            return render_template('auth/cadastro_organizador.html')
        
        if len(senha) < 6:
            flash('❌ A senha deve ter no mínimo 6 caracteres.', 'error')
            return render_template('auth/cadastro_organizador.html')
        
        # Criar novo organizador
        novo_usuario = Usuario(
            nome=nome,
            cpf=cpf,
            tipo='organizador'
        )
        novo_usuario.set_password(senha)
        
        try:
            db.session.add(novo_usuario)
            
            # Marcar CPF como usado
            pre_auth.marcar_como_usado()
            
            db.session.commit()
            
            flash('✅ Cadastro de organizador realizado com sucesso! Faça login.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Erro ao criar conta: {str(e)}', 'error')
            return render_template('auth/cadastro_organizador.html')
    
    return render_template('auth/cadastro_organizador.html')


@auth_bp.route('/verificar-cpf-organizador', methods=['POST'])
def verificar_cpf_organizador():
    """
    Endpoint AJAX para verificar se CPF está autorizado
    """
    cpf = request.json.get('cpf', '').strip()
    cpf = ''.join(filter(str.isdigit, cpf))
    
    if not Usuario.validar_cpf(cpf):
        return {'valido': False, 'mensagem': 'CPF inválido'}
    
    # Verificar autorização
    pre_auth = PreAuthorizedUser.cpf_autorizado(cpf, role='organizador')
    
    if pre_auth:
        return {'valido': True, 'mensagem': 'CPF autorizado para cadastro!'}
    else:
        return {'valido': False, 'mensagem': 'CPF não autorizado. Contate o administrador.'}