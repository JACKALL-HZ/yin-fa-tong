"""add guide_runs table

Revision ID: f1a2b3c4d5e6
Revises: ed91c680b5c9
Create Date: 2026-08-19
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'ed91c680b5c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tb_guide_runs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('trace_id', sa.String(length=64), nullable=False),
        sa.Column('thread_id', sa.String(length=64), nullable=False),
        sa.Column('symptom_text', sa.String(length=500), nullable=False),
        sa.Column('engine', sa.String(length=20), nullable=False, server_default='langgraph'),
        sa.Column('emergency_level', sa.String(length=10), nullable=False, server_default=''),
        sa.Column('extract_engine', sa.String(length=20), nullable=False, server_default=''),
        sa.Column('nodes_path', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('duration_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ok'),
        sa.Column('error', sa.String(length=500), nullable=True),
        sa.Column('nodes_detail', sa.Text(), nullable=True),
        sa.Column('create_time', sa.DateTime(), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('update_time', sa.DateTime(), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.Column('is_deleted', sa.Integer(), server_default='0', nullable=False, comment='0未删除 1已删除'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tb_guide_runs_trace_id', 'tb_guide_runs', ['trace_id'])
    op.create_index('ix_tb_guide_runs_thread_id', 'tb_guide_runs', ['thread_id'])


def downgrade() -> None:
    op.drop_index('ix_tb_guide_runs_thread_id', table_name='tb_guide_runs')
    op.drop_index('ix_tb_guide_runs_trace_id', table_name='tb_guide_runs')
    op.drop_table('tb_guide_runs')
