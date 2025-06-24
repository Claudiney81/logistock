# app/routes/baixa_campo.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import current_user
from datetime import datetime
from app.extensions import db
from app.models import (
    Tecnico, TipoServico, Item,
    EstoqueTecnico, BaixaAplicacaoCampo, BaixaAplicacaoCampoItem
)

bp_baixa = Blueprint('baixa_campo', __name__, url_prefix='/baixa_campo')

# -------------------------------------------------------------------------
# 1. Tela + POST de nova baixa
# -------------------------------------------------------------------------
@bp_baixa.route('/nova', methods=['GET', 'POST'])
def nova_baixa():
    tecnicos = Tecnico.query.order_by(Tecnico.nome).all()
    tipos_servico = TipoServico.query.order_by(TipoServico.nome).all()

    if request.method == 'POST':
        tecnico_id      = request.form.get('tecnico_id')
        tipo_servico_id = request.form.get('tipo_servico_id')
        local_servico   = request.form.get('local_servico')
        data_hora_str   = request.form.get('data_hora')
        observacao      = request.form.get('observacao')

        # -------- DateTime seguro ----------
        if data_hora_str:
            try:
                # input type=datetime-local → formato “YYYY-MM-DDTHH:MM”
                data_hora = datetime.fromisoformat(data_hora_str)
            except ValueError:
                data_hora = datetime.utcnow()
        else:
            data_hora = datetime.utcnow()
        # ------------------------------------

        codigos      = request.form.getlist('codigo[]')       # hidden no template
        quantidades  = request.form.getlist('quantidade[]')
        valores      = request.form.getlist('valor[]')

        baixa = BaixaAplicacaoCampo(
            tecnico_id     = tecnico_id,
            supervisor_id  = getattr(current_user, 'id', None),
            tipo_servico_id= tipo_servico_id,
            local_servico  = local_servico,
            data_hora      = data_hora,
            observacao     = observacao
        )
        db.session.add(baixa)
        db.session.flush()   # já gera baixa.id

        itens_recusados = []
        houve_sucesso   = False

        for idx, cod in enumerate(codigos):
            if not cod:
                continue

            item = Item.query.filter_by(codigo=cod, tipo_servico_id=tipo_servico_id).first()
            if not item:
                continue

            estoque_tecnico = EstoqueTecnico.query.filter_by(
                tecnico_id=tecnico_id,
                item_id=item.id,
                tipo_servico_id=tipo_servico_id
            ).first()

            qtd_baixa = int(quantidades[idx] or 0)

            if not estoque_tecnico or estoque_tecnico.quantidade < qtd_baixa or qtd_baixa <= 0:
                itens_recusados.append(
                    {'codigo': cod, 'quantidade': qtd_baixa, 'tecnico_id': tecnico_id,
                     'tipo_servico_id': tipo_servico_id}
                )
                flash(f"Saldo insuficiente do item {cod}!", "danger")
                continue

            # baixa efetiva
            estoque_tecnico.quantidade -= qtd_baixa

            db.session.add(BaixaAplicacaoCampoItem(
                baixa_id     = baixa.id,
                item_id      = item.id,
                quantidade   = qtd_baixa,
                valor_unitario = float(valores[idx] or 0)
            ))
            houve_sucesso = True

        # guarda recusados na sessão (pode ser usado para sugestão de transferência)
        if itens_recusados:
            session['itens_recusados'] = itens_recusados

        if not houve_sucesso:
            db.session.rollback()
            flash('Nenhuma baixa realizada. Corrija as quantidades e tente novamente.', 'danger')
            return redirect(url_for('baixa_campo.nova_baixa'))

        db.session.commit()
        flash('Baixa de materiais realizada com sucesso!', 'success')
        return redirect(url_for('baixa_campo.historico_baixas'))

    # GET
    return render_template('baixa_campo/nova_baixa.html',
                           tecnicos=tecnicos,
                           tipos_servico=tipos_servico)

# -------------------------------------------------------------------------
# 2. Histórico resumido
# -------------------------------------------------------------------------
@bp_baixa.route('/historico')
def historico_baixas():
    tecnicos       = Tecnico.query.order_by(Tecnico.nome).all()
    tipos_servico  = TipoServico.query.order_by(TipoServico.nome).all()
    tecnico_id     = request.args.get('tecnico_id')
    tipo_servico_id= request.args.get('tipo_servico_id')
    data_inicio    = request.args.get('data_inicio')
    data_fim       = request.args.get('data_fim')

    query = BaixaAplicacaoCampo.query
    if tecnico_id:
        query = query.filter_by(tecnico_id=tecnico_id)
    if tipo_servico_id:
        query = query.filter_by(tipo_servico_id=tipo_servico_id)
    if data_inicio:
        try:
            query = query.filter(BaixaAplicacaoCampo.data_hora >= datetime.strptime(data_inicio,'%Y-%m-%d'))
        except ValueError:
            pass
    if data_fim:
        try:
            query = query.filter(BaixaAplicacaoCampo.data_hora <= datetime.strptime(data_fim,'%Y-%m-%d'))
        except ValueError:
            pass

    baixas = query.order_by(BaixaAplicacaoCampo.data_hora.desc()).all()
    return render_template('baixa_campo/historico_baixas.html',
                           baixas=baixas,
                           tecnicos=tecnicos,
                           tipos_servico=tipos_servico)

# -------------------------------------------------------------------------
# 3. Listagem gerencial (baixas_realizadas)
# -------------------------------------------------------------------------
@bp_baixa.route('/baixas_realizadas')
def baixas_realizadas():
    tecnicos       = Tecnico.query.order_by(Tecnico.nome).all()
    tipos_servico  = TipoServico.query.order_by(TipoServico.nome).all()
    tecnico_id     = request.args.get('tecnico_id')
    tipo_servico_id= request.args.get('tipo_servico_id')
    data_inicio    = request.args.get('data_inicio')
    data_fim       = request.args.get('data_fim')

    query = BaixaAplicacaoCampo.query
    if tecnico_id:
        query = query.filter_by(tecnico_id=tecnico_id)
    if tipo_servico_id:
        query = query.filter_by(tipo_servico_id=tipo_servico_id)
    if data_inicio:
        try:
            query = query.filter(BaixaAplicacaoCampo.data_hora >= datetime.strptime(data_inicio,'%Y-%m-%d'))
        except ValueError:
            pass
    if data_fim:
        try:
            query = query.filter(BaixaAplicacaoCampo.data_hora <= datetime.strptime(data_fim,'%Y-%m-%d'))
        except ValueError:
            pass

    baixas = query.order_by(BaixaAplicacaoCampo.data_hora.desc()).all()
    return render_template('baixa_campo/baixas_realizadas.html',
                           baixas=baixas,
                           tecnicos=tecnicos,
                           tipos_servico=tipos_servico,
                           filtros={
                               'tecnico_id': tecnico_id,
                               'tipo_servico_id': tipo_servico_id,
                               'data_inicio': data_inicio,
                               'data_fim': data_fim
                           })

# -------------------------------------------------------------------------
# 4. API – saldo técnico por tipo de serviço (usado no template JS)
# -------------------------------------------------------------------------
@bp_baixa.route('/api/saldo_tecnico')
def api_saldo_tecnico():
    tecnico_id      = request.args.get('tecnico_id')
    tipo_servico_id = request.args.get('tipo_servico_id')

    saldos = (db.session.query(EstoqueTecnico, Item)
              .join(Item, EstoqueTecnico.item_id == Item.id)
              .filter(EstoqueTecnico.tecnico_id == tecnico_id,
                      EstoqueTecnico.tipo_servico_id == tipo_servico_id)
              .all())

    resultado = []
    for estoque_tecnico, item in saldos:
        resultado.append({
            'id'        : item.id,          # agora vai o ID também
            'codigo'    : item.codigo,
            'descricao' : item.descricao,
            'unidade'   : item.unidade,
            'quantidade': estoque_tecnico.quantidade,
            'valor'     : item.valor
        })

    return jsonify(resultado)
