from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime
import io
import pandas as pd
from flask import send_file
from flask import Blueprint

from app.extensions import db
from app.models import (
    RequisicaoTecnico,
    RequisicaoTecnicoItem,
    Tecnico,
    TipoServico,
    Item,
    Estoque,
)

bp_requisicoes_tecnicos = Blueprint(
    "requisicoes_tecnicos", __name__, url_prefix="/requisicoes_tecnicos"
)

# ---------------------------------------------------------------------------
# NOVA REQUISIÇÃO -----------------------------------------------------------
# ---------------------------------------------------------------------------


@bp_requisicoes_tecnicos.route("/nova", methods=["GET", "POST"])
@login_required
def nova_requisicao():
    """Formulário de criação de requisição (perfil técnico)."""
    if request.method == "POST":
        dados = request.form

        nova = RequisicaoTecnico(
            solicitante_responsavel=dados.get("solicitante_responsavel"),
            solicitante_tecnico=dados.get("solicitante_tecnico"),  # *nome textual*
            tipo_servico=dados.get("tipo_servico"),
            observacao=dados.get("observacao"),
            status="pendente",
        )
        db.session.add(nova)
        db.session.flush()  # garante nova.id

        # Itens
        for codigo, desc, unid, qtd, val, qtd_estoque in zip(
            dados.getlist("codigo[]"),
            dados.getlist("descricao[]"),
            dados.getlist("unidade[]"),
            dados.getlist("quantidade[]"),
            dados.getlist("valor[]"),
            dados.getlist("quantidade_estoque[]"),
        ):
            if codigo.strip():
                db.session.add(
                    RequisicaoTecnicoItem(
                        requisicao_id=nova.id,
                        codigo=codigo,
                        descricao=desc,
                        unidade=unid,
                        quantidade=int(qtd or 0),
                        valor=float(val or 0),
                        quantidade_estoque=int(qtd_estoque or 0),
                    )
                )

        db.session.commit()
        flash("Requisição cadastrada com sucesso!", "success")
        return redirect(url_for("requisicoes_tecnicos.recebidas"))

    tecnicos = Tecnico.query.order_by(Tecnico.nome).all()
    tipos_servico = TipoServico.query.order_by(TipoServico.nome).all()
    return render_template(
        "requisicoes_tecnicos/nova_requisicao.html",
        tecnicos=tecnicos,
        tipos_servico=tipos_servico,
    )


# ---------------------------------------------------------------------------
# LISTAGENS -----------------------------------------------------------------
# ---------------------------------------------------------------------------


@bp_requisicoes_tecnicos.route("/recebidas")
@login_required
def recebidas():
    requisicoes = (
        RequisicaoTecnico.query.filter_by(status="pendente")
        .order_by(RequisicaoTecnico.data_hora.desc())
        .all()
    )
    return render_template("requisicoes_tecnicos/recebidas.html", requisicoes=requisicoes)


@bp_requisicoes_tecnicos.route("/atendidas")
@login_required
def atendidas():
    requisicoes = (
        RequisicaoTecnico.query.filter_by(status="material_entregue")
        .order_by(RequisicaoTecnico.data_hora.desc())
        .all()
    )
    return render_template("requisicoes_tecnicos/atendidas.html", requisicoes=requisicoes)


@bp_requisicoes_tecnicos.route("/historico")
@login_required
def historico():
    requisicoes = (
        RequisicaoTecnico.query.order_by(RequisicaoTecnico.data_hora.desc()).all()
    )
    return render_template(
        "requisicoes_tecnicos/historico_requisicoes.html", requisicoes=requisicoes
    )


# ---------------------------------------------------------------------------
# DETALHES / EDIÇÃO ---------------------------------------------------------
# ---------------------------------------------------------------------------


@bp_requisicoes_tecnicos.route("/detalhes/<int:requisicao_id>", methods=["GET", "POST"])
@login_required
def detalhes(requisicao_id):
    requisicao = RequisicaoTecnico.query.get_or_404(requisicao_id)

    if request.method == "POST":
        requisicao.status = request.form.get("status")
        requisicao.observacao_estoque = request.form.get("observacao")
        db.session.commit()
        flash("Requisição atualizada com sucesso.", "success")
        return redirect(url_for("requisicoes_tecnicos.recebidas"))

    return render_template(
        "requisicoes_tecnicos/detalhes_requisicao.html", requisicao=requisicao
    )


# ---------------------------------------------------------------------------
# API – Busca de Item por código -------------------------------------------
# ---------------------------------------------------------------------------


@bp_requisicoes_tecnicos.route("/api/item/<codigo>")
@login_required
def api_item_por_codigo(codigo):
    tipo_servico_nome = request.args.get("tipo_servico")
    if not tipo_servico_nome:
        return jsonify({"erro": "Tipo de serviço não informado"}), 400

    item = (
        Item.query.join(TipoServico)
        .filter(Item.codigo == codigo.strip(), TipoServico.nome == tipo_servico_nome)
        .first()
    )
    if not item:
        return jsonify({"erro": "Item não encontrado"}), 404

    estoque = Estoque.query.filter_by(item_id=item.id).first()
    qtd_estoque = estoque.quantidade if estoque else 0

    return jsonify(
        {
            "descricao": item.descricao,
            "unidade": item.unidade,
            "valor": item.valor,
            "quantidade_estoque": qtd_estoque,
        }
    )

# ---------------------------------------------------------------------------
# EXCLUIR -------------------------------------------------------------------
# ---------------------------------------------------------------------------

@bp_requisicoes_tecnicos.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir(id):
    if current_user.perfil != "admin":
        flash("Você não tem permissão para excluir requisições.", "danger")
        return redirect(url_for("requisicoes_tecnicos.historico"))

    requisicao = RequisicaoTecnico.query.get_or_404(id)
    RequisicaoTecnicoItem.query.filter_by(requisicao_id=requisicao.id).delete()
    db.session.delete(requisicao)
    db.session.commit()
    flash("Requisição excluída com sucesso.", "success")
    return redirect(url_for("requisicoes_tecnicos.historico"))

@bp_requisicoes_tecnicos.route('/relatorio-consumo', methods=['GET', 'POST'])
@login_required
def relatorio_consumo():
    tecnicos = Tecnico.query.order_by(Tecnico.nome).all()
    resultados = []

    if request.method == 'POST':
        tecnico_nome = request.form.get("tecnico")
        codigo_item = request.form.get("codigo_item")
        data_inicio = request.form.get("data_inicio")
        data_fim = request.form.get("data_fim")

        query = (
            db.session.query(
                RequisicaoTecnicoItem.codigo,
                RequisicaoTecnicoItem.descricao,
                RequisicaoTecnicoItem.unidade,
                Tecnico.nome.label("nome_tecnico"),
                func.sum(RequisicaoTecnicoItem.quantidade).label("quantidade_total")
            )
            .join(RequisicaoTecnico, RequisicaoTecnicoItem.requisicao_id == RequisicaoTecnico.id)
            .join(Tecnico, RequisicaoTecnico.solicitante_tecnico_id == Tecnico.id)
            .filter(RequisicaoTecnico.status == "material_entregue")
        )

        if tecnico_nome and tecnico_nome != "todos":
            query = query.filter(Tecnico.nome == tecnico_nome)

        if codigo_item:
            query = query.filter(RequisicaoTecnicoItem.codigo == codigo_item)

        if data_inicio:
            data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
            query = query.filter(RequisicaoTecnico.data_hora >= data_inicio)

        if data_fim:
            data_fim = datetime.strptime(data_fim, "%Y-%m-%d")
            query = query.filter(RequisicaoTecnico.data_hora <= data_fim)

        resultados = query.group_by(
            RequisicaoTecnicoItem.codigo,
            RequisicaoTecnicoItem.descricao,
            RequisicaoTecnicoItem.unidade,
            Tecnico.nome
        ).order_by(Tecnico.nome, RequisicaoTecnicoItem.descricao).all()

    return render_template("requisicoes_tecnicos/relatorio_consumo.html", tecnicos=tecnicos, resultados=resultados)


@bp_requisicoes_tecnicos.route("/relatorio-consumo/exportar-excel", methods=["POST"])
@login_required
def exportar_excel():
    tecnico_nome = request.form.get("tecnico")
    codigo_item = request.form.get("codigo_item")
    data_inicio = request.form.get("data_inicio")
    data_fim = request.form.get("data_fim")

    query = (
        db.session.query(
            RequisicaoTecnicoItem.codigo,
            RequisicaoTecnicoItem.descricao,
            RequisicaoTecnicoItem.unidade,
            Tecnico.nome.label("nome_tecnico"),
            func.sum(RequisicaoTecnicoItem.quantidade).label("quantidade_total")
        )
        .join(RequisicaoTecnico, RequisicaoTecnicoItem.requisicao_id == RequisicaoTecnico.id)
        .join(Tecnico, RequisicaoTecnico.solicitante_tecnico_id == Tecnico.id)
        .filter(RequisicaoTecnico.status == "material_entregue")
    )

    if tecnico_nome and tecnico_nome != "todos":
        query = query.filter(Tecnico.nome == tecnico_nome)

    if codigo_item:
        query = query.filter(RequisicaoTecnicoItem.codigo == codigo_item)

    if data_inicio:
        data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
        query = query.filter(RequisicaoTecnico.data_hora >= data_inicio)

    if data_fim:
        data_fim = datetime.strptime(data_fim, "%Y-%m-%d")
        query = query.filter(RequisicaoTecnico.data_hora <= data_fim)

    resultados = query.group_by(
        RequisicaoTecnicoItem.codigo,
        RequisicaoTecnicoItem.descricao,
        RequisicaoTecnicoItem.unidade,
        Tecnico.nome
    ).order_by(Tecnico.nome, RequisicaoTecnicoItem.descricao).all()

    dados = [dict(
        Código=r.codigo,
        Descrição=r.descricao,
        Unidade=r.unidade,
        Técnico=r.nome_tecnico,
        Quantidade_Total=r.quantidade_total
    ) for r in resultados]

    df = pd.DataFrame(dados)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Consumo Técnico")

    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="relatorio_consumo.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
