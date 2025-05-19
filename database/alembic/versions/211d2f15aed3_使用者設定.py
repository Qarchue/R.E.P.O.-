"""使用者設定

Revision ID: 211d2f15aed3
Revises: 5a2e6f307bc1
Create Date: 2024-11-14 12:14:22.485682

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '211d2f15aed3'
down_revision: Union[str, None] = '5a2e6f307bc1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_configuration',
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.discord_id'), primary_key=True),
        sa.Column('group_password', sa.Integer(), nullable=True),
        sa.Column('steam_friend_code', sa.String(), nullable=True),
        sa.Column('limit_mode', sa.Integer(), nullable=False, server_default=0),
        sa.Column('user_limit', sa.Integer(), nullable=False, server_default=0),
    )

def downgrade() -> None:
    op.drop_table('user_configuration')