from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db
from app.models import Tecnico

bp = Blueprint('tecnicos', __name__, url_prefix='/tecnicos')  # mudou para bp

@bp.route('/cadastro', methods=['GET', 'POST'])
def cadastrar_tecnico():
    if request.method == 'POST':
        nome = request.form['nome']
        matricula = request.form['matricula']
        cpf = request.form['cpf']
        telefone = request.form['telefone']
        email = request.form['email']
        area_tecnica = request.form['area_tecnica']
        status = request.form['status']

        if not nome or not matricula or not cpf:
            flash('Nome, Matrícula e CPF são obrigatórios.', 'danger')
            return redirect(url_for('tecnicos.cadastrar_tecnico'))

        tecnico = Tecnico.query.filter_by(matricula=matricula).first()
        if tecnico:
            flash('Matrícula já cadastrada.', 'danger')
            return redirect(url_for('tecnicos.cadastrar_tecnico'))

        novo_tecnico = Tecnico(
            nome=nome,
            matricula=matricula,
            cpf=cpf,
            telefone=telefone,
            email=email,
            area_tecnica=area_tecnica,
            status=status
        )
        db.session.add(novo_tecnico)
        db.session.commit()
        flash('Técnico cadastrado com sucesso!', 'success')
        return redirect(url_for('tecnicos.listar_tecnicos'))

    return render_template('tecnicos/cadastro.html')

@bp.route('/listagem')
def listar_tecnicos():
    tecnicos = Tecnico.query.order_by(Tecnico.nome).all()
    return render_template('tecnicos/listagem.html', tecnicos=tecnicos)
