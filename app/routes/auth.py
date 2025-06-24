from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager
from app.models import Usuario
from flask_login import UserMixin

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Certifique-se que o model Usuario herda de UserMixin:
# class Usuario(db.Model, UserMixin):

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home.home'))

    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        user = Usuario.query.filter_by(email=email).first()
        if user and check_password_hash(user.senha_hash, senha):
            login_user(user)
            flash('Login efetuado com sucesso!', 'success')
            return redirect(url_for('home.home'))
        else:
            flash('Email ou senha inválidos.', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('home.home'))

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        perfil = request.form['perfil']

        if Usuario.query.filter_by(email=email).first():
            flash('Email já cadastrado.', 'warning')
            return redirect(url_for('auth.registro'))

        novo_usuario = Usuario(
            nome=nome,
            email=email,
            senha_hash=generate_password_hash(senha),
            perfil=perfil
        )
        db.session.add(novo_usuario)
        db.session.commit()
        flash('Usuário registrado com sucesso! Faça login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/registro.html')
