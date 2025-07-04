from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.extensions import db
from app.models import TransferenciaInterna, TransferenciaInternaItem, Tecnico, TipoServico, Item, Estoque, EstoqueTecnico
from datetime import datetime

bp_interna = Blueprint('transferencias_interna', __name__, url_prefix='/transferencias/interna')

@bp_interna.route('/nova', methods=['GET', 'POST'])
def nova_transferencia_interna():
    tecnicos = Tecnico.query.order_by(Tecnico.nome).all()
    tipos_servico = TipoServico.query.order_by(TipoServico.nome).all()

    if request.method == 'POST':
        tecnico_id = request.form.get('tecnico_id')
        area_tecnica = request.form.get('area_tecnica')
        tipo_servico_id = request.form.get('tipo_servico_id')

        codigos = request.form.getlist('codigo[]')
        descricoes = request.form.getlist('descricao[]')
        unidades = request.form.getlist('unidade[]')
        quantidades = request.form.getlist('quantidade[]')
        valores = request.form.getlist('valor_unitario[]')

        if not tecnico_id or not area_tecnica or not tipo_servico_id:
            flash("Preencha todos os campos do cabeçalho.", "danger")
            return redirect(url_for('transferencias_interna.nova_transferencia_interna'))

        nova_transf = TransferenciaInterna(
            tecnico_id=tecnico_id,
            area_tecnica=area_tecnica,
            tipo_servico_id=tipo_servico_id,
            data_hora=datetime.utcnow()
        )
        db.session.add(nova_transf)
        db.session.flush()

        sucesso = False  # Para saber se pelo menos um item foi transferido

        for i in range(len(codigos)):
            if not codigos[i] or not quantidades[i] or int(quantidades[i]) <= 0:
                continue

            item_obj = Item.query.filter_by(codigo=codigos[i], tipo_servico_id=tipo_servico_id).first()
            if not item_obj:
                continue

            estoque = Estoque.query.filter_by(item_id=item_obj.id).first()
            if not estoque:
                flash(f"Item {codigos[i]} não possui saldo cadastrado!", "danger")
                continue

            quantidade_transferida = int(quantidades[i])

            if estoque.quantidade < quantidade_transferida:
                flash(f"Saldo insuficiente para o item {codigos[i]}! Saldo disponível: {estoque.quantidade}", "danger")
                continue

            # Faz a baixa no saldo!
            estoque.quantidade -= quantidade_transferida

            item_transf = TransferenciaInternaItem(
                transferencia_interna_id=nova_transf.id,
                item_id=item_obj.id,
                quantidade=quantidade_transferida,
                valor_unitario=float(valores[i]) if valores[i] else 0
            )
            db.session.add(item_transf)

            # Atualiza o saldo no EstoqueTecnico
            estoque_tec = EstoqueTecnico.query.filter_by(
                tecnico_id=tecnico_id,
                item_id=item_obj.id,
                tipo_servico_id=tipo_servico_id
            ).first()

            if estoque_tec:
                estoque_tec.quantidade += quantidade_transferida
            else:
                estoque_tec = EstoqueTecnico(
                    tecnico_id=tecnico_id,
                    item_id=item_obj.id,
                    tipo_servico_id=tipo_servico_id,
                    quantidade=quantidade_transferida
                )
                db.session.add(estoque_tec)

            sucesso = True

        if not sucesso:
            db.session.rollback()
            flash("Nenhum item transferido. Corrija as quantidades e tente novamente.", "danger")
            return redirect(url_for('transferencias_interna.nova_transferencia_interna'))

        db.session.commit()
        flash("Transferência interna registrada com sucesso!", "success")
        return redirect(url_for('transferencias_interna.historico_transferencia_interna'))

    return render_template(
        'transferencias/interna/nova_transferencia_interna.html',
        tecnicos=tecnicos,
        tipos_servico=tipos_servico
    )

@bp_interna.route('/historico')
def historico_transferencia_interna():
    transferencias = TransferenciaInterna.query.order_by(TransferenciaInterna.data_hora.desc()).all()
    return render_template('transferencias/interna/historico_transferencia_interna.html', transferencias=transferencias)

@bp_interna.route('/detalhes/<int:id>')
def detalhes_transferencia_interna(id):
    transferencia = TransferenciaInterna.query.get_or_404(id)
    return render_template('transferencias/interna/detalhes.html', transferencia=transferencia)

# --- NOVA ROTA PARA CONSULTA DE ITEM + SALDO ---
@bp_interna.route('/api/item_saldo')
def api_item_saldo():
    codigo = request.args.get('codigo')
    tipo_servico_id = request.args.get('tipo_servico_id')
    if not codigo or not tipo_servico_id:
        return jsonify({'error': 'Código e Tipo de Serviço obrigatórios'}), 400

    item = Item.query.filter_by(codigo=codigo, tipo_servico_id=tipo_servico_id).first()
    if not item:
        return jsonify({'error': 'Item não encontrado'}), 404

    estoque = Estoque.query.filter_by(item_id=item.id).first()
    saldo = estoque.quantidade if estoque else 0

    return jsonify({
        'codigo': item.codigo,
        'descricao': item.descricao,
        'unidade': item.unidade,
        'valor': item.valor,
        'saldo': saldo
    })
