"""nullable elder_bind_id

Revision ID: a1b2c3d4e5f6
Revises: 08704cab3ae5
Create Date: 2026-06-22 22:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: str = 'a8c54db0eff6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        'tb_accompany_order', 'elder_bind_id',
        existing_type=sa.BigInteger(),
        nullable=True,
        existing_comment='陪同长辈ID，老人本人下单时可为空'
    )


def downgrade() -> None:
    op.alter_column(
        'tb_accompany_order', 'elder_bind_id',
        existing_type=sa.BigInteger(),
        nullable=False,
        existing_comment='陪同长辈ID'
    )
