"""白名單

Revision ID: baa0de9c0b00
Revises: ce327780e494
Create Date: 2025-05-04 14:58:44.677173

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'baa0de9c0b00'
down_revision: Union[str, None] = 'ce327780e494'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'white_list',
        sa.Column('discord_id', sa.Integer(), sa.ForeignKey('users.discord_id'), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.discord_id'), nullable=False),
    )

def downgrade() -> None:
    op.drop_table('white_list')