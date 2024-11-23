"""create auth tables

Revision ID: create_auth_tables
Revises: e68f0a1eced1
Create Date: 2024-11-22 13:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'create_auth_tables_001'  # Changed to ensure unique ID
down_revision = 'ee3942eb14cd'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Drop tables if they exist (to avoid conflicts)
    op.execute('DROP TABLE IF EXISTS auth_sessions')
    op.execute('DROP TABLE IF EXISTS service_accounts')
    
    op.create_table('service_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('domain', sa.String(255), nullable=False),
        sa.Column('description', sa.String(500)),
        sa.Column('permissions', sa.JSON()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('last_login', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=text('GETDATE()')),
        sa.Column('updated_at', sa.DateTime(), server_default=text('GETDATE()')),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('auth_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('service_account_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(500), unique=True),
        sa.Column('created_at', sa.DateTime(), server_default=text('GETDATE()')),
        sa.Column('expires_at', sa.DateTime()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.ForeignKeyConstraint(['service_account_id'], ['service_accounts.id']),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('auth_sessions')
    op.drop_table('service_accounts')