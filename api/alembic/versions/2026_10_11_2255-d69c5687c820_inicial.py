"""initial

Revision ID: d69c5687c820
Revises:
Create Date: 2026-10-11 22:55:41.585833
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d69c5687c820"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
