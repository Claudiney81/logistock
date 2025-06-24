from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from app import db
from app.models import Item, Estoque, TipoServico
import io
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask_login import login_required

bp = Blueprint('estoque', __name__, url_prefix='/estoque')
@login_required
# ------------------------
# Cadastro de Item Manual
# ------------------------
@bp.route('/cadastro', methods=['GET', 'POST'])
@login_required
def cadastrar_item():
    if request.method == 'POST':
        codigo = request.form['codigo']
        descricao = request.form['descricao']
        unidade = request.form['unidade']
        tipo_servico_id = request.form.get('tipo_servico_id')
        valor = float(request.form['valor'])

        if Item.query.filter_by(codigo=codigo).first():
            flash('Já existe um item com este código.', 'warning')
            return redirect(url_for('estoque.cadastrar_item'))

        # Garante que o tipo de serviço existe
        tipo_servico = TipoServico.query.get(tipo_servico_id)
        if not tipo_servico:
            flash('Tipo de Serviço inválido.', 'danger')
            return redirect(url_for('estoque.cadastrar_item'))

        novo_item = Item(
            codigo=codigo,
            descricao=descricao,
            unidade=unidade,
            tipo_servico_id=tipo_servico.id,
            valor=valor
        )
        db.session.add(novo_item)
        db.session.commit()
        flash('Item cadastrado com sucesso!', 'success')
        return redirect(url_for('estoque.cadastrar_item'))

    # Lista todos os tipos de serviço para o select do formulário
    tipos_servico = TipoServico.query.all()
    return render_template('estoque/cadastro.html', tipos_servico=tipos_servico)

# ------------------------
# Listar Itens (com Tipo de Serviço)
# ------------------------
@bp.route('/listar', methods=['GET'])
def listar_itens():
    codigo = request.args.get('codigo', '').strip()
    descricao = request.args.get('descricao', '').strip()
    tipo_servico = request.args.get('tipo_servico', '').strip()

    # Faz join com tipo_servico para filtrar pelo nome
    query = db.session.query(Item, TipoServico).join(TipoServico)

    if codigo:
        query = query.filter(Item.codigo.ilike(f'%{codigo}%'))
    if descricao:
        query = query.filter(Item.descricao.ilike(f'%{descricao}%'))
    if tipo_servico:
        query = query.filter(TipoServico.nome.ilike(f'%{tipo_servico}%'))

    itens = query.all()
    return render_template('estoque/listar.html', itens=itens, codigo=codigo, descricao=descricao, tipo_servico=tipo_servico)

# ------------------------
# Importar Itens via Excel
# ------------------------
@bp.route('/importar', methods=['POST'])
def importar_itens():
    arquivo = request.files.get('arquivo')

    if not arquivo:
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('estoque.cadastrar_item'))

    try:
        df = pd.read_excel(arquivo)
        for _, row in df.iterrows():
            codigo = str(row.get('Código', '')).strip()
            descricao = str(row.get('Descrição', '')).strip()
            unidade = str(row.get('Unidade', '')).strip()
            nome_tipo_servico = str(row.get('Tipo de Serviço', '')).strip()
            valor = float(row.get('Valor', 0))

            if not codigo or not descricao:
                continue

            # Garante tipo de serviço existente (cria se não houver)
            tipo_servico = TipoServico.query.filter_by(nome=nome_tipo_servico).first()
            if not tipo_servico:
                tipo_servico = TipoServico(nome=nome_tipo_servico, empresa='')
                db.session.add(tipo_servico)
                db.session.commit()

            if not Item.query.filter_by(codigo=codigo).first():
                item = Item(
                    codigo=codigo,
                    descricao=descricao,
                    unidade=unidade,
                    tipo_servico_id=tipo_servico.id,
                    valor=valor
                )
                db.session.add(item)
        db.session.commit()
        flash('Itens importados com sucesso.', 'success')
    except Exception as e:
        flash(f'Erro ao importar itens: {str(e)}', 'danger')

    return redirect(url_for('estoque.cadastrar_item'))

# ------------------------
# Saldo de Estoque (com Tipo de Serviço)
# ------------------------
@bp.route('/saldo', methods=['GET'])
def saldo_estoque():
    codigo = request.args.get('codigo', '').strip()
    descricao = request.args.get('descricao', '').strip()
    tipo_servico = request.args.get('tipo_servico', '').strip()

    # Corrigido: join explícito, evitando ambiguidade!
    query = db.session.query(Estoque, Item, TipoServico)\
        .select_from(Estoque)\
        .join(Item, Estoque.item_id == Item.id)\
        .join(TipoServico, Item.tipo_servico_id == TipoServico.id)

    if codigo:
        query = query.filter(Item.codigo.ilike(f'%{codigo}%'))
    if descricao:
        query = query.filter(Item.descricao.ilike(f'%{descricao}%'))
    if tipo_servico:
        query = query.filter(TipoServico.nome.ilike(f'%{tipo_servico}%'))

    resultados = query.all()

    return render_template(
        'estoque/saldo.html',
        resultados=resultados,
        codigo=codigo,
        descricao=descricao,
        tipo_servico=tipo_servico
    )
@bp.route('/alertas')
def alerta_estoque_baixo():
    query = db.session.query(Estoque, Item, TipoServico)\
        .select_from(Estoque)\
        .join(Item, Estoque.item_id == Item.id)\
        .join(TipoServico, Item.tipo_servico_id == TipoServico.id)\
        .filter(Estoque.quantidade <= Estoque.quantidade_minima)

    resultados = query.all()
    return render_template('estoque/alertas.html', resultados=resultados)

from flask import jsonify

@bp.route('/api/estoque_saldo/<int:tipo_servico_id>')
def api_estoque_saldo(tipo_servico_id):
    query = db.session.query(Estoque, Item)\
        .join(Item, Estoque.item_id == Item.id)\
        .filter(Item.tipo_servico_id == tipo_servico_id)

    resultados = []
    for estoque, item in query.all():
        resultados.append({
            'codigo': item.codigo,
            'descricao': item.descricao,
            'unidade': item.unidade,
            'quantidade': estoque.quantidade,
            'valor': item.valor
        })

    return jsonify(resultados)

@bp.route('/api/item_por_codigo/<codigo>')
def api_item_por_codigo(codigo):
    item = Item.query.filter_by(codigo=codigo).first()
    if not item:
        return jsonify({'error': 'Item não encontrado'}), 404
    return jsonify({
        'codigo': item.codigo,
        'descricao': item.descricao,
        'unidade': item.unidade,
        'valor': item.valor
    })

