"""伺服器設定

Revision ID: 22226be4d55d
Revises: 211d2f15aed3
Create Date: 2024-11-15 13:23:20.752792

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '22226be4d55d'
down_revision: Union[str, None] = '211d2f15aed3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'server_configuration',
        sa.Column('server_id', sa.Integer(), sa.ForeignKey('servers.server_id'), primary_key=True),
        sa.Column('looking_for_group_channel', sa.Integer(), nullable=True),
        sa.Column('thread_id', sa.Integer(), nullable=True),
        sa.Column('create_group_button', sa.Integer(), nullable=True),
        sa.Column('waiting_room_channel', sa.Integer(), nullable=True),
        sa.Column('steamAPI_key', sa.String(), nullable=True),
    )

def downgrade() -> None:
    op.drop_table('server_configuration')