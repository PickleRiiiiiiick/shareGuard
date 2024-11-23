"""add missing fields to scan target

Revision ID: add_missing_fields_002
Revises: create_auth_tables_001
Create Date: 2024-11-23 19:47:10.007000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'add_missing_fields_002'  # Following your numbering convention
down_revision = 'create_auth_tables_001'  # This refers to your previous migration
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add new columns to scan_targets table
    with op.batch_alter_table('scan_targets') as batch_op:
        # Adding description field
        batch_op.add_column(sa.Column('description', sa.String(500), nullable=True))
        
        # Adding department field
        batch_op.add_column(sa.Column('department', sa.String(100), nullable=True))
        
        # Adding owner field
        batch_op.add_column(sa.Column('owner', sa.String(100), nullable=True))
        
        # Adding sensitivity level field
        batch_op.add_column(sa.Column('sensitivity_level', sa.String(50), nullable=True))
        
        # Adding target metadata field (renamed from metadata to avoid SQLAlchemy conflicts)
        batch_op.add_column(sa.Column('target_metadata', sa.JSON, nullable=True))
        
        # Adding created_by field
        batch_op.add_column(sa.Column('created_by', sa.String(100), nullable=True))
        
        # Ensure created_at has a default value if it doesn't already
        batch_op.alter_column('created_at',
                            existing_type=sa.DateTime(),
                            server_default=text('GETDATE()'),
                            nullable=False)

def downgrade() -> None:
    # Remove added columns in reverse order
    with op.batch_alter_table('scan_targets') as batch_op:
        batch_op.drop_column('created_by')
        batch_op.drop_column('target_metadata')
        batch_op.drop_column('sensitivity_level')
        batch_op.drop_column('owner')
        batch_op.drop_column('department')
        batch_op.drop_column('description')
        
        # Reset created_at to original state if needed
        batch_op.alter_column('created_at',
                            existing_type=sa.DateTime(),
                            server_default=None)