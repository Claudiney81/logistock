from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import NotaFiscalEntrada, NotaFiscalItem, Item, Estoque, TipoServico
from datetime import datetime

bp = Blueprint('nota_fiscal', __name__, url_prefix='/nota')

@bp.route('/nova', methods=['GET', 'POST'])
def nova_nota():
    if request.method == 'POST':
        numero_nf = request.form['numero_nf']
        reserva = request.form['reserva']
        tipo_servico_id = request.form['tipo_servico_id']  # Recebe o ID do select
        responsavel = request.form['responsavel']
        observacao = request.form['observacao']
        itens = request.form.getlist('codigo[]')
        quantidades = request.form.getlist('quantidade[]')
        valores = request.form.getlist('valor[]')

        # Busca o NOME do tipo de serviço para salvar (pois o model não é FK!)
        tipo_servico_obj = TipoServico.query.get(tipo_servico_id)
        tipo_servico_nome = tipo_servico_obj.nome if tipo_servico_obj else ''

        nota_existente = NotaFiscalEntrada.query.filter_by(numero_nf=numero_nf).first()
        if nota_existente:
            flash('Já existe uma nota fiscal com este número.', 'danger')
            return redirect(url_for('nota_fiscal.nova_nota'))

        nova_nota = NotaFiscalEntrada(
            numero_nf=numero_nf,
            reserva=reserva,
            tipo_servico=tipo_servico_nome,  # <--- Aqui agora vai o nome!
            responsavel=responsavel,
            observacao=observacao,
            data_hora=datetime.utcnow()
        )
        db.session.add(nova_nota)
        db.session.flush()

        for codigo, qtd, val in zip(itens, quantidades, valores):
            item = Item.query.filter_by(codigo=codigo).first()
            if item:
                novo_item = NotaFiscalItem(
                    nota_fiscal_id=nova_nota.id,
                    item_id=item.id,
                    quantidade=int(qtd),
                    valor_unitario=float(val)
                )
                db.session.add(novo_item)

                estoque = Estoque.query.filter_by(item_id=item.id).first()
                if estoque:
                    estoque.quantidade += int(qtd)
                else:
                    novo_estoque = Estoque(item_id=item.id, quantidade=int(qtd), quantidade_minima=0)
                    db.session.add(novo_estoque)

        db.session.commit()
        flash('Registro com sucesso!', 'success')
        return redirect(url_for('nota_fiscal.historico'))

    itens = Item.query.all()
    tipos_servico = TipoServico.query.all()
    return render_template('nota_fiscal/nova.html', itens=itens, tipos_servico=tipos_servico)

@bp.route('/historico')
def historico():
    tipo_servico = request.args.get('tipo_servico', '').strip()
    query = NotaFiscalEntrada.query
    if tipo_servico:
        query = query.filter(NotaFiscalEntrada.tipo_servico.ilike(f'%{tipo_servico}%'))
    notas = query.order_by(NotaFiscalEntrada.data_hora.desc()).all()
    return render_template('nota_fiscal/historico.html', notas=notas, tipo_servico=tipo_servico)

@bp.route('/<int:id>')
def detalhes(id):
    nota = NotaFiscalEntrada.query.get_or_404(id)
    return render_template('nota_fiscal/detalhes.html', nota=nota)

@bp.route('/pesquisar', methods=['GET'])
def pesquisar():
    termo = request.args.get('query', '').strip()
    query = NotaFiscalEntrada.query
    if termo:
        query = query.filter(
            (NotaFiscalEntrada.numero_nf.ilike(f'%{termo}%')) |
            (NotaFiscalEntrada.reserva.ilike(f'%{termo}%'))
        )
    notas = query.order_by(NotaFiscalEntrada.data_hora.desc()).all()

    if len(notas) == 1:
        return redirect(url_for('nota_fiscal.detalhes', id=notas[0].id))
    elif len(notas) == 0:
        flash('Nenhuma nota encontrada com os critérios fornecidos.', 'warning')
        return redirect(url_for('nota_fiscal.pesquisar'))
    else:
        return render_template('nota_fiscal/pesquisar.html', notas=notas, termo=termo)

@bp.route('/excluir/<int:id>', methods=['POST'])
def excluir_nota(id):
    nota = NotaFiscalEntrada.query.get_or_404(id)

    for item_nf in nota.itens:
        estoque = Estoque.query.filter_by(item_id=item_nf.item_id).first()
        if estoque:
            estoque.quantidade -= item_nf.quantidade
            if estoque.quantidade < 0:
                estoque.quantidade = 0

    NotaFiscalItem.query.filter_by(nota_fiscal_id=nota.id).delete()
    db.session.delete(nota)
    db.session.commit()
    flash('Nota fiscal excluída com sucesso.', 'success')
    return redirect(url_for('nota_fiscal.historico'))

@bp.route('/buscar_item')
def buscar_item():
    codigo = request.args.get('codigo')
    item = Item.query.filter_by(codigo=codigo).first()
    if item:
        return {
            'success': True,
            'descricao': item.descricao,
            'valor': item.valor,
            'tipo_servico': item.tipo_servico_rel.nome if item.tipo_servico_rel else ''
        }
    return {'success': False}
