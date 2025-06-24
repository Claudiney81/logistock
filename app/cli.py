import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models import Item, Empresa, TipoServico, Usuario
from werkzeug.security import generate_password_hash

@click.command("init-db")
@with_appcontext
def init_db():
    db.create_all()
    click.echo("Tabelas criadas com sucesso.")

@click.command("seed-dados")
@with_appcontext
def seed_dados():
    if not TipoServico.query.filter_by(nome='GPON MDU F').first():
        tipo1 = TipoServico(nome='GPON MDU F', empresa='Empresa A')
        tipo2 = TipoServico(nome='REDE INTERNA', empresa='Empresa B')
        db.session.add_all([tipo1, tipo2])
        db.session.commit()
        click.echo("Tipos de serviço adicionados.")

    tipo_fibra = TipoServico.query.filter_by(nome='GPON MDU F').first()

    if not Item.query.filter_by(codigo='A123').first():
        item1 = Item(codigo='A123', descricao='Cabo de Fibra', unidade='m', tipo_servico_id=tipo_fibra.id, valor=10.5)
        item2 = Item(codigo='B456', descricao='Conector Óptico', unidade='un', tipo_servico_id=tipo_fibra.id, valor=2.75)
        db.session.add_all([item1, item2])
        click.echo("Itens adicionados.")

    if not Empresa.query.filter_by(cnpj='12.345.678/0001-90').first():
        empresa1 = Empresa(
            razao_social='Parceiro Instalações LTDA',
            cnpj='12.345.678/0001-90',
            endereco='Rua das Instalações, 123',
            contato='(11) 99999-0001',
            tipo_servico='instalação',
            observacoes='Empresa terceirizada de instalação'
        )
        empresa2 = Empresa(
            razao_social='Manutenção Total ME',
            cnpj='98.765.432/0001-10',
            endereco='Av. Manutenção, 456',
            contato='(11) 88888-0002',
            tipo_servico='manutenção',
            observacoes='Responsável por manutenção preventiva'
        )
        db.session.add_all([empresa1, empresa2])
        click.echo("Empresas adicionadas.")

    db.session.commit()
    click.echo("Seed concluído.")

@click.command("criar-usuario")
@with_appcontext
def criar_usuario():
    nome = click.prompt("Nome completo")
    email = click.prompt("Email")
    senha = click.prompt("Senha", hide_input=True, confirmation_prompt=True)
    perfil = click.prompt("Perfil", type=click.Choice(['admin', 'estoque', 'tecnico'], case_sensitive=False))

    if Usuario.query.filter_by(email=email).first():
        click.echo("Esse e-mail já está em uso.")
        return

    novo = Usuario(
        nome=nome,
        email=email,
        senha_hash=generate_password_hash(senha),
        perfil=perfil
    )
    db.session.add(novo)
    db.session.commit()
    click.echo(f"Usuário '{email}' criado com sucesso.")

@click.command("editar-usuario")
@click.argument("email")
@with_appcontext
def editar_usuario(email):
    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario:
        click.echo(f"Usuário com e-mail '{email}' não encontrado.")
        return

    novo_nome = click.prompt("Novo nome", default=usuario.nome)
    nova_senha = click.prompt("Nova senha", hide_input=True, confirmation_prompt=True)
    novo_perfil = click.prompt("Novo perfil", type=click.Choice(['admin', 'estoque', 'tecnico'], case_sensitive=False), default=usuario.perfil)

    usuario.nome = novo_nome
    usuario.senha_hash = generate_password_hash(nova_senha)
    usuario.perfil = novo_perfil

    db.session.commit()
    click.echo(f"Usuário '{email}' atualizado com sucesso.")

@click.command("listar-usuarios")
@with_appcontext
def listar_usuarios():
    usuarios = Usuario.query.all()
    if not usuarios:
        click.echo("Nenhum usuário encontrado.")
        return
    for u in usuarios:
        click.echo(f"Email: {u.email}, Nome: {u.nome}, Perfil: {u.perfil}")

@click.command("deletar-usuario")
@click.argument("email")
@with_appcontext
def deletar_usuario(email):
    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario:
        click.echo("Usuário não encontrado.")
        return
    db.session.delete(usuario)
    db.session.commit()
    click.echo(f"Usuário '{email}' excluído.")
