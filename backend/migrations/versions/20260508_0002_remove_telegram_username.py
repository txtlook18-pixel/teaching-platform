"""remove telegram_username from users

Revision ID: 20260508_0002
Revises: 20260505_0001
Create Date: 2026-05-08 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260508_0002"
down_revision: Union[str, None] = "20260505_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("users", "telegram_username")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column("telegram_username", sa.String(length=255), nullable=True),
    )
