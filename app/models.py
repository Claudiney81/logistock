from datetime import datetime
from app.extensions import db
from flask_login import UserMixin

# =======================
# MODELO DE TIPOS DE SERVIÇO
# =======================

class TipoServico(db.Model):
    __tablename__ = 'tipos_servico'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    empresa = db.Column(db.String(100))
    itens = db.relationship('Item', backref='tipo_servico_rel', lazy=True)

# =======================
# MODELO DE ITENS E ESTOQUE GERAL
# =======================

class Item(db.Model):
    __tablename__ = 'itens'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    unidade = db.Column(db.String(20), nullable=False)
    tipo_servico_id = db.Column(db.Integer, db.ForeignKey('tipos_servico.id'))
    valor = db.Column(db.Float, nullable=False)
    observacoes = db.Column(db.Text)

class Estoque(db.Model):
    __tablename__ = 'estoque'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('itens.id'), nullable=False)
    quantidade = db.Column(db.Integer, default=0)
    quantidade_minima = db.Column(db.Integer, default=0)
    item = db.relationship('Item', backref='estoques')

# =======================
# ESTOQUE DO TÉCNICO
# =======================

class EstoqueTecnico(db.Model):
    __tablename__ = 'estoque_tecnico'
    id = db.Column(db.Integer, primary_key=True)
    tecnico_id = db.Column(db.Integer, db.ForeignKey('tecnicos.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('itens.id'), nullable=False)
    tipo_servico_id = db.Column(db.Integer, db.ForeignKey('tipos_servico.id'), nullable=False)
    quantidade = db.Column(db.Integer, default=0)
    tecnico = db.relationship('Tecnico')
    item = db.relationship('Item')
    tipo_servico = db.relationship('TipoServico')

# =======================
# NOVA FUNCIONALIDADE: REQUISIÇÕES TÉCNICOS
# =======================

class RequisicaoTecnico(db.Model):
    __tablename__ = 'requisicoes_tecnicos'
    id = db.Column(db.Integer, primary_key=True)
    solicitante_responsavel = db.Column(db.String(100), nullable=False)
    solicitante_tecnico = db.Column(db.String(100), nullable=False)
    solicitante_tecnico_id = db.Column(db.Integer, db.ForeignKey('tecnicos.id'))
    tecnico_rel = db.relationship('Tecnico', foreign_keys=[solicitante_tecnico_id])
    tipo_servico = db.Column(db.String(100), nullable=False)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    observacao = db.Column(db.Text)
    status = db.Column(db.String(20), default="Pendente")
    observacao_estoque = db.Column(db.Text)
    itens = db.relationship("RequisicaoTecnicoItem", backref="requisicao", lazy=True, cascade="all, delete-orphan")

class RequisicaoTecnicoItem(db.Model):
    __tablename__ = 'requisicoes_tecnicos_itens'
    id = db.Column(db.Integer, primary_key=True)
    requisicao_id = db.Column(db.Integer, db.ForeignKey("requisicoes_tecnicos.id"), nullable=False)
    codigo = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    unidade = db.Column(db.String(20), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor = db.Column(db.Float, nullable=False)
    quantidade_estoque = db.Column(db.Integer)

# =======================
# NOTAS FISCAIS DE ENTRADA
# =======================

class NotaFiscalEntrada(db.Model):
    __tablename__ = 'notas_fiscais_entrada'
    id = db.Column(db.Integer, primary_key=True)
    numero_nf = db.Column(db.String(50), nullable=False)
    reserva = db.Column(db.String(50))
    tipo_servico = db.Column(db.String(100))
    responsavel = db.Column(db.String(100))
    observacao = db.Column(db.Text)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    itens = db.relationship('NotaFiscalItem', backref='nota_fiscal', cascade='all, delete-orphan')

class NotaFiscalItem(db.Model):
    __tablename__ = 'notas_fiscais_itens'
    id = db.Column(db.Integer, primary_key=True)
    nota_fiscal_id = db.Column(db.Integer, db.ForeignKey('notas_fiscais_entrada.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('itens.id'))
    quantidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Float, nullable=False)
    item = db.relationship('Item', backref='notas_fiscais_itens')

# =======================
# EMPRESAS PARCEIRAS
# =======================

class Empresa(db.Model):
    __tablename__ = 'empresas'
    id = db.Column(db.Integer, primary_key=True)
    razao_social = db.Column(db.String(120), nullable=False)
    cnpj = db.Column(db.String(20), nullable=False)
    endereco = db.Column(db.String(255))
    contato = db.Column(db.String(100))
    tipo_servico = db.Column(db.String(100))
    observacoes = db.Column(db.Text)
    transferencias = db.relationship('TransferenciaExterna', backref='empresa', cascade='all, delete-orphan')

# =======================
# TRANSFERÊNCIA EXTERNA
# =======================

class TransferenciaExterna(db.Model):
    __tablename__ = 'transferencias_externas'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    autorizado_por = db.Column(db.String(100), nullable=False)
    retirado_por = db.Column(db.String(100), nullable=False)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    itens = db.relationship('TransferenciaItem', backref='transferencia', cascade='all, delete-orphan')

class TransferenciaItem(db.Model):
    __tablename__ = 'transferencias_itens'
    id = db.Column(db.Integer, primary_key=True)
    transferencia_id = db.Column(db.Integer, db.ForeignKey('transferencias_externas.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('itens.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Float, nullable=False)
    item = db.relationship('Item')

# =======================
# TECNICOS
# =======================

class Tecnico(db.Model):
    __tablename__ = 'tecnicos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    matricula = db.Column(db.String(50), unique=True, nullable=False)
    cpf = db.Column(db.String(20), unique=True, nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    area_tecnica = db.Column(db.String(100))
    status = db.Column(db.String(20), default='Ativo')

    # Relacionamento com saldo técnico
    estoque_tecnico = db.relationship('EstoqueTecnico', backref='tecnico_rel', lazy=True)

    def __repr__(self):
        return f"<Tecnico {self.nome} - {self.matricula}>"

# =======================
# KIT INICIAL
# =======================

class KitInicial(db.Model):
    __tablename__ = 'kits_iniciais'
    id = db.Column(db.Integer, primary_key=True)
    nome_kit = db.Column(db.String(150), nullable=False)
    tecnico_id = db.Column(db.Integer, db.ForeignKey('tecnicos.id'), nullable=False)
    tipo_servico_id = db.Column(db.Integer, db.ForeignKey('tipos_servico.id'), nullable=False)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    observacao = db.Column(db.Text)
    tecnico = db.relationship('Tecnico', backref='kits_iniciais')
    tipo_servico = db.relationship('TipoServico')
    itens = db.relationship('KitInicialItem', backref='kit_inicial', cascade='all, delete-orphan')

class KitInicialItem(db.Model):
    __tablename__ = 'kits_iniciais_itens'
    id = db.Column(db.Integer, primary_key=True)
    kit_inicial_id = db.Column(db.Integer, db.ForeignKey('kits_iniciais.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('itens.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Float, nullable=False)
    item = db.relationship('Item')

# =======================
# TRANSFERÊNCIA INTERNA
# =======================

class TransferenciaInterna(db.Model):
    __tablename__ = 'transferencias_internas'
    id = db.Column(db.Integer, primary_key=True)
    tecnico_id = db.Column(db.Integer, db.ForeignKey('tecnicos.id'), nullable=False)
    area_tecnica = db.Column(db.String(100), nullable=False)
    tipo_servico_id = db.Column(db.Integer, db.ForeignKey('tipos_servico.id'), nullable=False)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    tecnico = db.relationship('Tecnico', backref='transferencias_internas')
    tipo_servico = db.relationship('TipoServico')
    itens = db.relationship('TransferenciaInternaItem', backref='transferencia_interna', cascade='all, delete-orphan')

class TransferenciaInternaItem(db.Model):
    __tablename__ = 'transferencias_internas_itens'
    id = db.Column(db.Integer, primary_key=True)
    transferencia_interna_id = db.Column(db.Integer, db.ForeignKey('transferencias_internas.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('itens.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Float, nullable=False)
    item = db.relationship('Item')

# =======================
# BAIXA DE MATERIAIS APLICADOS EM CAMPO
# =======================

class BaixaAplicacaoCampo(db.Model):
    __tablename__ = 'baixa_aplicacao_campo'
    id = db.Column(db.Integer, primary_key=True)
    tecnico_id = db.Column(db.Integer, db.ForeignKey('tecnicos.id'), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    tipo_servico_id = db.Column(db.Integer, db.ForeignKey('tipos_servico.id'))
    local_servico = db.Column(db.String(255))
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    observacao = db.Column(db.Text)
    itens = db.relationship('BaixaAplicacaoCampoItem', backref='baixa', cascade='all, delete-orphan')
    tecnico = db.relationship('Tecnico')
    tipo_servico = db.relationship('TipoServico')

class BaixaAplicacaoCampoItem(db.Model):
    __tablename__ = 'baixa_aplicacao_campo_itens'
    id = db.Column(db.Integer, primary_key=True)
    baixa_id = db.Column(db.Integer, db.ForeignKey('baixa_aplicacao_campo.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('itens.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Float)
    item = db.relationship('Item')

# =======================
# USUÁRIOS DO SISTEMA
# =======================

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    perfil = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='Ativo')

    def __repr__(self):
        return f"<Usuario {self.nome} ({self.email})>"
# =======================
# BAIXAS MANUAIS DO SALDO TÉCNICO
# =======================

class BaixaTecnica(db.Model):
    __tablename__ = 'baixas_tecnicas'
    id = db.Column(db.Integer, primary_key=True)
    tecnico_id = db.Column(db.Integer, db.ForeignKey('tecnicos.id'), nullable=False)
    tipo_servico_id = db.Column(db.Integer, db.ForeignKey('tipos_servico.id'), nullable=False)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)

    tecnico = db.relationship('Tecnico', backref='baixas_tecnicas')
    tipo_servico = db.relationship('TipoServico')
    itens = db.relationship('BaixaTecnicaItem', backref='baixa_tecnica', cascade='all, delete-orphan')


class BaixaTecnicaItem(db.Model):
    __tablename__ = 'baixas_tecnicas_itens'
    id = db.Column(db.Integer, primary_key=True)
    baixa_tecnica_id = db.Column(db.Integer, db.ForeignKey('baixas_tecnicas.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('itens.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    item = db.relationship('Item')

