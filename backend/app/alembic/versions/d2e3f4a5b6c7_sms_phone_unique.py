"""add unique constraint to phone

Revision ID: d2e3f4a5b6c7
Revises: 29202f402497
Create Date: 2026-06-27 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'd2e3f4a5b6c7'
down_revision: Union[str, None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 先将 phone 字段设为可空（如果还不是的话），因为手机号登录时新用户可能先创建再设置
    op.alter_column('tb_user', 'phone', existing_type=sa.String(length=20), nullable=True)
    # 添加 unique 约束
    op.create_unique_constraint('uq_tb_user_phone', 'tb_user', ['phone'])


def downgrade() -> None:
    op.drop_constraint('uq_tb_user_phone', 'tb_user', type_='unique')
