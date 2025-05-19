"""黑名單

Revision ID: ce327780e494
Revises: 22226be4d55d
Create Date: 2025-05-04 14:58:39.586098

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce327780e494'
down_revision: Union[str, None] = '22226be4d55d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'black_list',
        sa.Column('discord_id', sa.Integer(), sa.ForeignKey('users.discord_id'), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.discord_id'), nullable=False),
    )


def downgrade():
    op.drop_table('black_list')