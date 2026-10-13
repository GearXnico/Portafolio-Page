"""daily visitor salt: generated at random each day and deleted the next

Revision ID: 8c537beb136d
Revises: a9c47c1ef041
Create Date: 2026-10-12 00:59:12.656714
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8c537beb136d"
down_revision: str | Sequence[str] | None = "a9c47c1ef041"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "visitor_salt",
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("salt", sa.LargeBinary(), nullable=False),
        sa.CheckConstraint("octet_length(salt) = 32", name=op.f("ck_visitor_salt_salt_length")),
        sa.PrimaryKeyConstraint("day", name=op.f("pk_visitor_salt")),
    )


def downgrade() -> None:
    op.drop_table("visitor_salt")
