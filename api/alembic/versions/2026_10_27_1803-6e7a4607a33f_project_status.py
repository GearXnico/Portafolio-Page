"""project status: optional, shown as a stamp on the page

Revision ID: 6e7a4607a33f
Revises: 8c537beb136d
Create Date: 2026-10-27 18:03:46.495324
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "6e7a4607a33f"
down_revision: str | Sequence[str] | None = "8c537beb136d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("project", sa.Column("status", sa.Text(), nullable=True))
    op.create_check_constraint(
        op.f("ck_project_status"), "project", "status IN ('done', 'in_progress')"
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_project_status"), "project", type_="check")
    op.drop_column("project", "status")
