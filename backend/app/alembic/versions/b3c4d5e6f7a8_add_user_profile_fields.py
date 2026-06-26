"""add_user_profile_fields

Revision ID: b3c4d5e6f7a8
Revises: 29202f402497
Create Date: 2026-06-23 20:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, None] = '29202f402497'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tb_user', sa.Column('real_name', sa.String(length=32), nullable=True, comment='真实姓名'))
    op.add_column('tb_user', sa.Column('gender', sa.Integer(), nullable=True, comment='1男 2女'))
    op.add_column('tb_user', sa.Column('id_card', sa.String(length=20), nullable=True, comment='身份证号'))
    op.add_column('tb_user', sa.Column('birthday', sa.Date(), nullable=True, comment='出生日期'))
    op.add_column('tb_user', sa.Column('phone', sa.String(length=20), nullable=True, comment='联系电话'))


def downgrade() -> None:
    op.drop_column('tb_user', 'phone')
    op.drop_column('tb_user', 'birthday')
    op.drop_column('tb_user', 'id_card')
    op.drop_column('tb_user', 'gender')
    op.drop_column('tb_user', 'real_name')
