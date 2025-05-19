"""標籤

Revision ID: d59e8617181b
Revises: b8ca0b6d1872
Create Date: 2025-05-16 15:06:38.469388

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd59e8617181b'
down_revision: Union[str, None] = 'b8ca0b6d1872'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'server_tags',
        sa.Column('server_id', sa.Integer(), sa.ForeignKey('servers.server_id'), primary_key=True),
        sa.Column('no_mods', sa.Integer(), nullable=True),
        sa.Column('custom_tags', sa.JSON(), default=dict, nullable=True),
        sa.Column('versions', sa.JSON(), default=dict, nullable=True),
    )


def downgrade() -> None:
    op.drop_table('server_tags')
