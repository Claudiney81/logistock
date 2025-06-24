from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from datetime import datetime
from app.models import Tecnico, EstoqueTecnico, TipoServico
from app.extensions import db
import pandas as pd
import io

bp = Blueprint('saldo_tecnico', __name__)

# Página principal com listagem dos técnicos
@bp.route('/saldo_tecnico')
def exibir_saldo():
    termo_busca = request.args.get('tecnico', '').strip()
    tecnicos = Tecnico.query.order_by(Tecnico.nome).all()

    if termo_busca:
        tecnicos = [t for t in tecnicos if termo_busca.lower() in t.nome.lower()]

    return render_template('saldo_tecnico.html', tecnicos=tecnicos, termo_busca=termo_busca)

# Página de saldo detalhado de um técnico
@bp.route('/saldo_tecnico/<int:id_tecnico>', methods=['GET'])
def saldo_detalhado(id_tecnico):
    tecnico = Tecnico.query.get_or_404(id_tecnico)
    saldos = EstoqueTecnico.query.filter_by(tecnico_id=id_tecnico).all()
    return render_template('saldo_tecnico_detalhado.html', tecnico=tecnico, saldos=saldos)

# Exporta o saldo de um técnico para Excel
@bp.route('/saldo_tecnico/<int:id_tecnico>/exportar', methods=['GET'])
def exportar_saldo_tecnico(id_tecnico):
    tecnico = Tecnico.query.get_or_404(id_tecnico)
    saldos = EstoqueTecnico.query.filter_by(tecnico_id=id_tecnico).all()

    dados = []
    for s in saldos:
        dados.append({
            'Código': s.item.codigo,
            'Descrição': s.item.descricao,
            'Unidade': s.item.unidade,
            'Tipo de Serviço': s.tipo_servico.nome if s.tipo_servico else '',
            'Quantidade': s.quantidade
        })

    df = pd.DataFrame(dados)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Saldo Técnico')

    output.seek(0)
    nome_arquivo = f"saldo_tecnico_{tecnico.nome.replace(' ', '_')}.xlsx"
    return send_file(output, download_name=nome_arquivo, as_attachment=True)
