from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models import Item, Estoque, db  # certifique-se que o db esteja sendo importado

bp = Blueprint('itens', __name__, url_prefix='/itens')

@bp.route('/buscar_item', methods=['GET'])
def buscar_item():
    codigo = request.args.get('codigo', '').strip().upper()
    item = Item.query.filter_by(codigo=codigo).first()
    if not item:
        return jsonify({'erro': 'Item não encontrado'}), 404

    estoque = Estoque.query.filter_by(item_id=item.id).first()
    quantidade = estoque.quantidade if estoque else 0

    if quantidade <= 0:
        return jsonify({'erro': 'Sem saldo em estoque!'}), 404

    return jsonify({
        'descricao': item.descricao,
        'unidade': item.unidade,
        'valor': item.valor,
        'quantidade': quantidade
    })

# ---- NOVAS ROTAS ----

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    item = Item.query.get_or_404(id)
    if request.method == 'POST':
        item.descricao = request.form['descricao']
        item.unidade = request.form['unidade']
        item.valor = request.form['valor']
        db.session.commit()
        flash('Item editado com sucesso!', 'success')
        return redirect(url_for('estoque.listar_itens'))  # ajuste conforme seu endpoint

    return render_template('itens/editar.html', item=item)

@bp.route('/excluir/<int:id>', methods=['POST', 'GET'])
def excluir(id):
    item = Item.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Item excluído com sucesso!', 'success')
    return redirect(url_for('estoque.listar_itens'))  # ajuste conforme seu endpoint
