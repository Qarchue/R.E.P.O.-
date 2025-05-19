"""group

Revision ID: b8ca0b6d1872
Revises: bda24c377cd7
Create Date: 2025-05-08 12:17:13.793307

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8ca0b6d1872'
down_revision: Union[str, None] = 'bda24c377cd7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'group',
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.discord_id'), primary_key=True, nullable=False),
        sa.Column('server_id', sa.Integer(), sa.ForeignKey('servers.server_id'), primary_key=True, nullable=False),
        sa.Column('voice_channel_id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('thread_id', sa.Integer(), nullable=False),
        sa.Column('description_message_id', sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('group')
