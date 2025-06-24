from app import create_app
from app.extensions import db
from app.models import Item, Empresa, TipoServico  # <-- Incluído TipoServico

app = create_app()

with app.app_context():
    db.create_all()
    print("Tabelas criadas com sucesso!")

    # Adicionar itens de exemplo
    if not Item.query.filter_by(codigo='A123').first():
        item1 = Item(codigo='A123', descricao='Cabo de Fibra', unidade='m', tipo_servico='fibra', valor=10.5, observacoes='')
        item2 = Item(codigo='B456', descricao='Conector Óptico', unidade='un', tipo_servico='fibra', valor=2.75, observacoes='')
        db.session.add_all([item1, item2])
        db.session.commit()
        print("Itens de exemplo adicionados.")
    else:
        print("Itens já existem — nada foi adicionado.")

    # Adicionar empresas de exemplo
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
        db.session.commit()
        print("Empresas de exemplo adicionadas.")
    else:
        print("Empresas já existem — nada foi adicionado.")

    # Adicionar tipos de serviço de exemplo
    if not TipoServico.query.filter_by(nome='GPON MDU F').first():
        tipo1 = TipoServico(nome='GPON MDU F', empresa='Empresa A')
        tipo2 = TipoServico(nome='REDE INTERNA', empresa='Empresa B')
        db.session.add_all([tipo1, tipo2])
        db.session.commit()
        print("Tipos de serviço adicionados.")
    else:
        print("Tipos de serviço já existem — nada foi adicionado.")
