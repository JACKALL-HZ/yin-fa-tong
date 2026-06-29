"""merge sms_phone_unique with main

Revision ID: ed91c680b5c9
Revises: c1d2e3f4a5b6, d2e3f4a5b6c7
Create Date: 2026-06-28 21:57:22.684556
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed91c680b5c9'
down_revision: Union[str, None] = ('c1d2e3f4a5b6', 'd2e3f4a5b6c7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
