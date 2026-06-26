"""add alipay_user_id to tb_user

Revision ID: c1d2e3f4a5b6
Revises: b3c4d5e6f7a8
Create Date: 2026-06-24 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tb_user', sa.Column('alipay_user_id', sa.String(length=128), nullable=True, comment='支付宝用户唯一标识'))
    op.create_unique_constraint('uq_tb_user_alipay_user_id', 'tb_user', ['alipay_user_id'])


def downgrade() -> None:
    op.drop_constraint('uq_tb_user_alipay_user_id', 'tb_user', type_='unique')
    op.drop_column('tb_user', 'alipay_user_id')
