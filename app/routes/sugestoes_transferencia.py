# app/routes/sugestoes_transferencia.py

from flask import Blueprint, render_template, session, redirect, url_for
from app.models import Item, TipoServico, Tecnico

bp_sugestao = Blueprint('sugestao_transferencia', __name__, url_prefix='/sugestao_transferencia')

@bp_sugestao.route('/')
def exibir_sugestoes():
    itens_recusados = session.get('itens_recusados', [])

    if not itens_recusados:
        return render_template('sugestoes_transferencia.html', sugestoes=None)

    sugestoes = []
    for item in itens_recusados:
        item_obj = Item.query.filter_by(codigo=item['codigo'], tipo_servico_id=item['tipo_servico_id']).first()
        tipo_servico = TipoServico.query.get(item['tipo_servico_id'])
        tecnico = Tecnico.query.get(item['tecnico_id'])

        if item_obj and tipo_servico and tecnico:
            sugestoes.append({
                'codigo': item['codigo'],
                'descricao': item_obj.descricao,
                'unidade': item_obj.unidade,
                'quantidade': item['quantidade'],
                'valor': item_obj.valor,
                'tipo_servico': tipo_servico.nome,
                'tecnico': tecnico.nome
            })

    return render_template('sugestoes_transferencia.html', sugestoes=sugestoes)

@bp_sugestao.route('/limpar')
def limpar_sugestoes():
    session.pop('itens_recusados', None)
    return redirect(url_for('sugestao_transferencia.exibir_sugestoes'))
