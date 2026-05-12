"""add sources_metadata to lessons

Revision ID: 20260512_0003
Revises: 20260508_0002
Create Date: 2026-05-12 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260512_0003"
down_revision: Union[str, None] = "20260508_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "lessons",
        sa.Column("sources_metadata", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("lessons", "sources_metadata")
