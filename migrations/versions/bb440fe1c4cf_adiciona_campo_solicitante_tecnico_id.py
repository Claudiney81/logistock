"""Adiciona campo solicitante_tecnico_id

Revision ID: bb440fe1c4cf
Revises: 47c691dd7fbd
Create Date: 2025-06-22 19:51:18.875734

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bb440fe1c4cf'
down_revision = '47c691dd7fbd'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('requisicoes_tecnicos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('solicitante_tecnico_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_requisicoes_tecnicos_solicitante_tecnico_id',
            'tecnicos',
            ['solicitante_tecnico_id'],
            ['id']
        )


def downgrade():
    with op.batch_alter_table('requisicoes_tecnicos', schema=None) as batch_op:
        batch_op.drop_constraint('fk_requisicoes_tecnicos_solicitante_tecnico_id', type_='foreignkey')
        batch_op.drop_column('solicitante_tecnico_id')
