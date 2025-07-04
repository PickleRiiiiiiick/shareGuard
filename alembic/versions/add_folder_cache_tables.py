"""add folder permission cache tables

Revision ID: cache_001
Revises: add_missing_fields_002
Create Date: 2025-01-03 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mssql

# revision identifiers, used by Alembic.
revision = 'cache_001'
down_revision = 'add_missing_fields_002'
branch_labels = None
depends_on = None


def upgrade():
    # Create folder_permission_cache table
    op.create_table('folder_permission_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('folder_path', sa.String(length=500), nullable=False),
        sa.Column('permissions_data', sa.JSON(), nullable=False),
        sa.Column('owner_info', sa.JSON(), nullable=True),
        sa.Column('inheritance_enabled', sa.Boolean(), nullable=True),
        sa.Column('last_scan_time', sa.DateTime(), nullable=True),
        sa.Column('last_modified_time', sa.DateTime(), nullable=True),
        sa.Column('is_stale', sa.Boolean(), nullable=True),
        sa.Column('scan_job_id', sa.Integer(), nullable=True),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_folder_permission_cache_folder_path'), 'folder_permission_cache', ['folder_path'], unique=True)
    op.create_index(op.f('ix_folder_permission_cache_id'), 'folder_permission_cache', ['id'], unique=False)
    op.create_index('idx_folder_path_stale', 'folder_permission_cache', ['folder_path', 'is_stale'], unique=False)
    op.create_index('idx_last_scan_time', 'folder_permission_cache', ['last_scan_time'], unique=False)
    op.create_index('idx_updated_at', 'folder_permission_cache', ['updated_at'], unique=False)
    
    # Create folder_structure_cache table
    op.create_table('folder_structure_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('root_path', sa.String(length=500), nullable=False),
        sa.Column('max_depth', sa.Integer(), nullable=False),
        sa.Column('structure_data', sa.JSON(), nullable=False),
        sa.Column('total_folders', sa.Integer(), nullable=True),
        sa.Column('scan_duration_ms', sa.Integer(), nullable=True),
        sa.Column('last_scan_time', sa.DateTime(), nullable=True),
        sa.Column('is_stale', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_folder_structure_cache_id'), 'folder_structure_cache', ['id'], unique=False)
    op.create_index(op.f('ix_folder_structure_cache_root_path'), 'folder_structure_cache', ['root_path'], unique=False)
    op.create_index('idx_root_depth', 'folder_structure_cache', ['root_path', 'max_depth'], unique=False)
    op.create_index('idx_structure_stale', 'folder_structure_cache', ['root_path', 'is_stale'], unique=False)


def downgrade():
    # Drop indexes and tables
    op.drop_index('idx_structure_stale', table_name='folder_structure_cache')
    op.drop_index('idx_root_depth', table_name='folder_structure_cache')
    op.drop_index(op.f('ix_folder_structure_cache_root_path'), table_name='folder_structure_cache')
    op.drop_index(op.f('ix_folder_structure_cache_id'), table_name='folder_structure_cache')
    op.drop_table('folder_structure_cache')
    
    op.drop_index('idx_updated_at', table_name='folder_permission_cache')
    op.drop_index('idx_last_scan_time', table_name='folder_permission_cache')
    op.drop_index('idx_folder_path_stale', table_name='folder_permission_cache')
    op.drop_index(op.f('ix_folder_permission_cache_id'), table_name='folder_permission_cache')
    op.drop_index(op.f('ix_folder_permission_cache_folder_path'), table_name='folder_permission_cache')
    op.drop_table('folder_permission_cache')