# app/routes/baixas_realizadas.py

from flask import render_template, request
from app.models import Tecnico, TipoServico, BaixaTecnica
from app.extensions import db
from sqlalchemy import and_
from datetime import datetime

# Importa o Blueprint já definido em baixa_campo.py
from .baixa_campo import bp_baixa

@bp_baixa.route('/baixas_realizadas', methods=['GET'])
def baixas_realizadas():
    tecnicos = Tecnico.query.order_by(Tecnico.nome).all()
    tipos_servico = TipoServico.query.order_by(TipoServico.nome).all()

    tecnico_id = request.args.get('tecnico_id')
    tipo_servico_id = request.args.get('tipo_servico_id')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')

    query = BaixaTecnica.query

    if tecnico_id:
        query = query.filter_by(tecnico_id=tecnico_id)
    if tipo_servico_id:
        query = query.filter_by(tipo_servico_id=tipo_servico_id)
    if data_inicio:
        try:
            inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(BaixaTecnica.data_hora >= inicio)
        except ValueError:
            pass
    if data_fim:
        try:
            fim = datetime.strptime(data_fim, '%Y-%m-%d')
            query = query.filter(BaixaTecnica.data_hora <= fim)
        except ValueError:
            pass

    baixas = query.order_by(BaixaTecnica.data_hora.desc()).all()

    # Agrupar os itens baixados
    itens_agrupados = {}

    for baixa in baixas:
        for item in baixa.itens:
            key = (item.codigo, item.descricao, item.unidade)
            if key not in itens_agrupados:
                itens_agrupados[key] = 0
            itens_agrupados[key] += item.quantidade

    return render_template(
        'baixa_campo/baixas_realizadas.html',
        tecnicos=tecnicos,
        tipos_servico=tipos_servico,
        itens_agrupados=itens_agrupados,
        filtros={
            'tecnico_id': tecnico_id,
            'tipo_servico_id': tipo_servico_id,
            'data_inicio': data_inicio,
            'data_fim': data_fim
        }
    )
