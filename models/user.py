from extensions import db
from flask_login import UserMixin  

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    ativo = db.Column(db.Boolean, default=True)  

