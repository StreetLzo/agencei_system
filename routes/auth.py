from flask import Blueprint, render_template, redirect, url_for, flash, request
from extensions import db
from models.user import User
from werkzeug.security import generate_password_hash, check_password_hash   
from flask_login import login_user 

auth_bp = Blueprint("auth", __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cpf = request.form['cpf']
        senha = request.form['senha']

        user = User.query.filter_by(cpf=cpf, ativo=True).first()

        if not user or not check_password_hash(user.senha):
          flash("CPF ou senha incorretos.", "danger")
          return redirect(url_for("auth.login"))


        login_user(user)
        return redirect('/')

    return render_template("login.html")