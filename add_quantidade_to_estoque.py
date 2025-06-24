from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        db.session.execute(text('ALTER TABLE estoque ADD COLUMN quantidade INTEGER DEFAULT 0'))
        db.session.commit()
        print("✅ Coluna 'quantidade' adicionada com sucesso na tabela 'estoque'.")
    except Exception as e:
        print("⚠️ Não foi possível adicionar a coluna (talvez ela já exista):")
        print(e)
