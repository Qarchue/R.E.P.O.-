"""使用者紀錄

Revision ID: bda24c377cd7
Revises: baa0de9c0b00
Create Date: 2025-05-07 15:44:45.336644

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bda24c377cd7'
down_revision: Union[str, None] = 'baa0de9c0b00'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_record',
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.discord_id'), primary_key=True),
        sa.Column('voice_name', sa.Integer(), nullable=True),
        sa.Column('group_name', sa.Integer(), nullable=True),
        sa.Column('group_description', sa.Integer(), nullable=True),
        sa.Column('mod_code', sa.Integer(), nullable=True),
        sa.Column('game_password', sa.Integer(), nullable=True),
        sa.Column('create_count', sa.String(), nullable=False, server_default="0"),
    )

def downgrade() -> None:
    op.drop_table('user_record')