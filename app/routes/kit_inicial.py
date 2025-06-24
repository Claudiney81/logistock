from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.extensions import db
from app.models import Tecnico, TipoServico, Item, Estoque, KitInicial, KitInicialItem
from datetime import datetime
import json

kit_inicial_bp = Blueprint('kit_inicial', __name__, url_prefix='/kit_inicial')

@kit_inicial_bp.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar_kit():
    tecnicos = Tecnico.query.order_by(Tecnico.nome).all()
    tipos_servico = TipoServico.query.order_by(TipoServico.nome).all()
    itens = []

    if request.method == 'POST':
        data = request.form
        nome_kit = data.get('nome_kit')
        tecnico_id = data.get('tecnico_id')
        tipo_servico_id = data.get('tipo_servico_id')
        observacao = data.get('observacao')
        itens_json = data.get('itens_json')

        if not nome_kit or not tecnico_id or not tipo_servico_id or not itens_json:
            flash('Preencha todos os campos obrigatórios e insira itens.', 'danger')
            return redirect(url_for('kit_inicial.cadastrar_kit'))

        itens = json.loads(itens_json)

        novo_kit = KitInicial(
            nome_kit=nome_kit,
            tecnico_id=tecnico_id,
            tipo_servico_id=tipo_servico_id,
            observacao=observacao,
            data_hora=datetime.utcnow()
        )
        db.session.add(novo_kit)
        db.session.flush()  # para ter id do kit antes do commit

        for i in itens:
            item_obj = Item.query.filter_by(codigo=i['codigo'], tipo_servico_id=tipo_servico_id).first()
            if not item_obj:
                continue
            quantidade = int(i['quantidade'])
            if quantidade <= 0:
                continue

            # Ajusta o estoque - baixa do estoque geral
            estoque = Estoque.query.filter_by(item_id=item_obj.id).first()
            if estoque:
                estoque.quantidade = max(estoque.quantidade - quantidade, 0)

            kit_item = KitInicialItem(
                kit_inicial_id=novo_kit.id,
                item_id=item_obj.id,
                quantidade=quantidade,
                valor_unitario=item_obj.valor
            )
            db.session.add(kit_item)

        db.session.commit()
        flash('Kit inicial transferido com sucesso!', 'success')
        return redirect(url_for('kit_inicial.historico_kits'))

    return render_template('kit_inicial/cadastrar.html', tecnicos=tecnicos, tipos_servico=tipos_servico)

@kit_inicial_bp.route('/historico')
def historico_kits():
    kits = KitInicial.query.order_by(KitInicial.data_hora.desc()).all()
    return render_template('kit_inicial/historico.html', kits=kits)

@kit_inicial_bp.route('/detalhes/<int:id>')
def detalhes_kit(id):
    kit = KitInicial.query.get_or_404(id)
    return render_template('kit_inicial/detalhes.html', kit=kit)

# NOVA ROTA API: traz todos os itens do tipo de serviço (mesmo saldo 0)
@kit_inicial_bp.route('/api/itens_por_tipo_servico/<int:tipo_servico_id>')
def api_itens_por_tipo_servico(tipo_servico_id):
    itens = db.session.query(Item, Estoque)\
        .outerjoin(Estoque, Item.id == Estoque.item_id)\
        .filter(Item.tipo_servico_id == tipo_servico_id).all()
    resultado = []
    for item, estoque in itens:
        resultado.append({
            'codigo': item.codigo,
            'descricao': item.descricao,
            'unidade': item.unidade,
            'quantidade_disponivel': estoque.quantidade if estoque else 0,
            'valor': item.valor
        })
    return jsonify(resultado)
