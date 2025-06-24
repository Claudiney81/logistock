from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db
from app.models import Empresa
from flask_login import login_required

empresas_bp = Blueprint('empresas', __name__, url_prefix='/empresas')

@empresas_bp.route('/')
@login_required
def lista_empresas():
    termo = request.args.get('busca', '').strip()
    if termo:
        empresas = Empresa.query.filter(
            (Empresa.razao_social.ilike(f"%{termo}%")) |
            (Empresa.cnpj.ilike(f"%{termo}%"))
        ).all()
    else:
        empresas = Empresa.query.all()
    return render_template('empresas/lista_empresas.html', empresas=empresas)

@empresas_bp.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar_empresa():
    if request.method == 'POST':
        nova_empresa = Empresa(
            razao_social=request.form['razao_social'],
            cnpj=request.form['cnpj'],
            endereco=request.form.get('endereco'),
            contato=request.form.get('contato'),
            tipo_servico=request.form.get('tipo_servico'),
            observacoes=request.form.get('observacoes')
        )
        db.session.add(nova_empresa)
        db.session.commit()
        flash('Empresa cadastrada com sucesso!', 'success')
        return redirect(url_for('empresas.lista_empresas'))

    return render_template('empresas/cadastro_empresa.html')

@empresas_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    if request.method == 'POST':
        empresa.razao_social = request.form['razao_social']
        empresa.cnpj = request.form['cnpj']
        empresa.endereco = request.form.get('endereco')
        empresa.contato = request.form.get('contato')
        empresa.tipo_servico = request.form.get('tipo_servico')
        empresa.observacoes = request.form.get('observacoes')

        db.session.commit()
        flash('Empresa editada com sucesso!', 'success')
        return redirect(url_for('empresas.lista_empresas'))

    return render_template('empresas/cadastro_empresa.html', empresa=empresa)

@empresas_bp.route('/excluir/<int:id>', methods=['POST'])
def excluir_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    db.session.delete(empresa)
    db.session.commit()
    flash('Empresa excluída com sucesso!', 'success')
    return redirect(url_for('empresas.lista_empresas'))
