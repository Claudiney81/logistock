from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from app.extensions import db
from app.models import Empresa, TransferenciaExterna, TransferenciaItem, Item, Estoque, TipoServico
import json

bp_externa = Blueprint('transferencia_externa', __name__, url_prefix='/transferencias/externa')

@bp_externa.route('/')
def nova_transferencia_externa():
    empresas = Empresa.query.all()

    tipos_servico = (
        db.session.query(TipoServico)
        .join(Item, TipoServico.id == Item.tipo_servico_id)
        .join(Estoque, Estoque.item_id == Item.id)
        .filter(Estoque.quantidade > 0)
        .distinct()
        .all()
    )

    return render_template(
        'transferencias/externa/nova_transferencia.html',
        empresas=empresas,
        tipos_servico=tipos_servico
    )

@bp_externa.route('/historico')
def historico_transferencia_externa():
    transferencias = TransferenciaExterna.query.order_by(TransferenciaExterna.data_hora.desc()).all()
    empresas = Empresa.query.order_by(Empresa.razao_social).all()
    return render_template('transferencias/externa/historico_transferencias.html', transferencias=transferencias, empresas=empresas)

@bp_externa.route('/empresa/<int:id>')
def obter_dados_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    return jsonify({
        'cnpj': empresa.cnpj,
        'endereco': empresa.endereco,
        'contato': empresa.contato
    })

@bp_externa.route('/detalhes/<int:id>')
def detalhes_transferencia_externa(id):
    transferencia = TransferenciaExterna.query.get_or_404(id)
    itens = transferencia.itens
    return render_template(
        'transferencias/externa/detalhes_transferencia.html',
        transferencia=transferencia,
        itens=itens
    )

@bp_externa.route('/registrar', methods=['POST'])
def registrar_transferencia_externa():
    data = request.form
    empresa_id = int(data.get('empresa_id'))
    autorizado_por = data.get('autorizado_por')
    retirado_por = data.get('retirado_por')
    tipo_servico = data.get('tipo_servico')
    itens_json = data.get('itens_json')
    itens = json.loads(itens_json) if itens_json else []

    transferencia = TransferenciaExterna(
        empresa_id=empresa_id,
        autorizado_por=autorizado_por,
        retirado_por=retirado_por,
        tipo_servico=tipo_servico
    )
    db.session.add(transferencia)
    db.session.commit()

    for i in itens:
        item_obj = Item.query.filter_by(codigo=i['codigo']).first()
        if not item_obj:
            continue
        quantidade = int(i['quantidade'])
        estoque = Estoque.query.filter_by(item_id=item_obj.id).first()
        if estoque:
            estoque.quantidade = max(estoque.quantidade - quantidade, 0)
        item_transferido = TransferenciaItem(
            transferencia_id=transferencia.id,
            item_id=item_obj.id,
            quantidade=quantidade,
            valor_unitario=item_obj.valor
        )
        db.session.add(item_transferido)

    db.session.commit()

    flash('Transferência registrada com sucesso!', 'success')
    return redirect(url_for('transferencia_externa.historico_transferencia_externa'))
