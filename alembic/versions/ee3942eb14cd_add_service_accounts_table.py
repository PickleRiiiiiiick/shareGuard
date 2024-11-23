"""add_service_accounts_table

Revision ID: ee3942eb14cd
Revises: e68f0a1eced1
Create Date: 2024-11-22 12:35:04.489460

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ee3942eb14cd'
down_revision: Union[str, None] = 'e68f0a1eced1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'service_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('domain', sa.String(255), nullable=False),
        sa.Column('description', sa.String(500)),
        sa.Column('permissions', sa.JSON()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('last_login', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username', 'domain', name='uq_service_account')
    )



def downgrade() -> None:
    op.drop_table('service_accounts')

