from flask import Blueprint, request, jsonify
from flask_login import login_required
from extensions import db
from models.pre_authorized_user import PreAuthorizedUser 
from utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/pre_authorized_users', methods=['POST'])
@login_required
@admin_required
def listar_pre_autorizados():
    usuarios = PreAuthorizedUser.query.all()

    return jsonify([{
        'id': user.id,
        'cpf': user.cpf,
        'nome': user.nome,
        'role': user.role,
        'usado': user.usado
    } for u in usuarios])   


@admin_bp.route('/pre_authorized_users', methods=['POST'])
@login_required
@admin_required

def adicionar_pre_autorizado():
    data = request.get_json()
    cpf = data.get('cpf')
    nome = data.get('nome')
    role = data.get('role')

    if not cpf or not nome or not role:
        return jsonify({'error': 'Dados incompletos.'}), 400
    
    if PreAuthorizedUser.query.filter_by(cpf=cpf).first():
        return jsonify({'error': 'CPF já autorizado.'}), 400 
    
    novo = PreAuthorizedUser(
        cpf=cpf,
        nome=nome, 
        role=role
    )

    db.session.add(novo)
    db.session.commit()

    return {'message': 'CPF pré-autorizado adicionado com sucesso.'}, 201