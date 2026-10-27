"""profile palette: optional colour palette of the page, chosen in the panel

Revision ID: 83be4cc739e5
Revises: 6e7a4607a33f
Create Date: 2026-10-27 18:08:27.793441
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "83be4cc739e5"
down_revision: str | Sequence[str] | None = "6e7a4607a33f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("profile", sa.Column("palette", sa.Text(), nullable=True))
    op.create_check_constraint(
        op.f("ck_profile_palette"),
        "profile",
        "palette IN ('mint', 'ice', 'neon-blue', 'ice-neon', 'glacier', 'lavender', 'crimson', "
        "'amber')",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_profile_palette"), "profile", type_="check")
    op.drop_column("profile", "palette")
