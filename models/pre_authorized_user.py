from extensions import db

class PreAuthorizedUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    nome = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    usado = db.Column(db.Boolean, default=False)