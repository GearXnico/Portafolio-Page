"""base models: profile, skills, experience, projects, screenshots, visits and messages

Revision ID: a9c47c1ef041
Revises: d69c5687c820
Create Date: 2026-10-12 00:27:54.020501
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a9c47c1ef041"
down_revision: str | Sequence[str] | None = "d69c5687c820"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "contact_message",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("lang", sa.Text(), nullable=False),
        sa.Column("utm_source", sa.Text(), nullable=True),
        sa.Column("utm_campaign", sa.Text(), nullable=True),
        sa.Column("read", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("emailed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint(
            "char_length(email) <= 320 AND email ~ '^[^@\\s]+@[^@\\s]+$'",
            name=op.f("ck_contact_message_email"),
        ),
        sa.CheckConstraint("lang IN ('es', 'en')", name=op.f("ck_contact_message_lang")),
        sa.CheckConstraint(
            "char_length(message) BETWEEN 1 AND 5000",
            name=op.f("ck_contact_message_message_length"),
        ),
        sa.CheckConstraint(
            "char_length(name) BETWEEN 1 AND 200", name=op.f("ck_contact_message_name_length")
        ),
        sa.CheckConstraint(
            "char_length(utm_source) <= 200 AND char_length(utm_campaign) <= 200",
            name=op.f("ck_contact_message_utm_length"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contact_message")),
    )
    op.create_table(
        "experience",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company", sa.Text(), nullable=False),
        sa.Column("role_es", sa.Text(), nullable=False),
        sa.Column("role_en", sa.Text(), nullable=False),
        sa.Column("description_es", sa.Text(), server_default="", nullable=False),
        sa.Column("description_en", sa.Text(), server_default="", nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.CheckConstraint(
            "end_date IS NULL OR end_date >= start_date", name=op.f("ck_experience_dates")
        ),
        sa.CheckConstraint("position >= 0", name=op.f("ck_experience_position")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_experience")),
    )
    op.create_table(
        "profile",
        sa.Column("id", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("headline_es", sa.Text(), nullable=False),
        sa.Column("headline_en", sa.Text(), nullable=False),
        sa.Column("about_es", sa.Text(), nullable=False),
        sa.Column("about_en", sa.Text(), nullable=False),
        sa.Column("contact_email", sa.Text(), nullable=False),
        sa.Column(
            "links",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("id = 1", name=op.f("ck_profile_single_row")),
        sa.CheckConstraint(
            "jsonb_typeof(links) = 'object' AND NOT jsonb_path_exists("
            'links, \'strict $.* ? (@.type() != "string" || !(@ like_regex "^https://[^[:space:]/]+[^[:space:]]*$"))\')',
            name=op.f("ck_profile_links_https"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_profile")),
    )
    op.create_table(
        "project",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("title_es", sa.Text(), nullable=False),
        sa.Column("title_en", sa.Text(), nullable=False),
        sa.Column("summary_es", sa.Text(), nullable=False),
        sa.Column("summary_en", sa.Text(), nullable=False),
        sa.Column("body_es", sa.Text(), server_default="", nullable=False),
        sa.Column("body_en", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "stack", postgresql.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False
        ),
        sa.Column("demo_url", sa.Text(), nullable=True),
        sa.Column("repo_url", sa.Text(), nullable=True),
        sa.Column("visible", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "char_length(demo_url) <= 2048 AND demo_url ~ '^https://[^[:space:]/]+[^[:space:]]*$'",
            name=op.f("ck_project_demo_url"),
        ),
        sa.CheckConstraint(
            "char_length(repo_url) <= 2048 AND repo_url ~ '^https://[^[:space:]/]+[^[:space:]]*$'",
            name=op.f("ck_project_repo_url"),
        ),
        sa.CheckConstraint(
            "slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name=op.f("ck_project_slug_format")
        ),
        sa.CheckConstraint("position >= 0", name=op.f("ck_project_position")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project")),
        sa.UniqueConstraint("slug", name=op.f("uq_project_slug")),
    )
    op.create_table(
        "skill",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.CheckConstraint(
            "category IN ('language', 'framework', 'tool')", name=op.f("ck_skill_category")
        ),
        sa.CheckConstraint("position >= 0", name=op.f("ck_skill_position")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_skill")),
    )
    op.create_table(
        "visit",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("utm_source", sa.Text(), nullable=True),
        sa.Column("utm_medium", sa.Text(), nullable=True),
        sa.Column("utm_campaign", sa.Text(), nullable=True),
        sa.Column("utm_content", sa.Text(), nullable=True),
        sa.Column("country", sa.Text(), nullable=True),
        sa.Column("lang", sa.Text(), nullable=False),
        sa.Column("referrer", sa.Text(), nullable=True),
        sa.Column("visitor_hash", sa.Text(), nullable=False),
        sa.CheckConstraint("country ~ '^[A-Z]{2}$'", name=op.f("ck_visit_country")),
        sa.CheckConstraint("lang IN ('es', 'en')", name=op.f("ck_visit_lang")),
        sa.CheckConstraint("visitor_hash ~ '^[0-9a-f]{64}$'", name=op.f("ck_visit_visitor_hash")),
        sa.CheckConstraint("char_length(referrer) <= 2048", name=op.f("ck_visit_referrer_length")),
        sa.CheckConstraint(
            "char_length(utm_source) <= 200 AND char_length(utm_medium) <= 200"
            " AND char_length(utm_campaign) <= 200 AND char_length(utm_content) <= 200",
            name=op.f("ck_visit_utm_length"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_visit")),
    )
    op.create_index(op.f("ix_visit_created_at"), "visit", ["created_at"], unique=False)
    op.create_table(
        "project_image",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("alt_es", sa.Text(), server_default="", nullable=False),
        sa.Column("alt_en", sa.Text(), server_default="", nullable=False),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.CheckConstraint(
            "path ~ '^[A-Za-z0-9_-][A-Za-z0-9_./-]*$' AND path !~ '\\.\\.'",
            name=op.f("ck_project_image_path"),
        ),
        sa.CheckConstraint("position >= 0", name=op.f("ck_project_image_position")),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["project.id"],
            name=op.f("fk_project_image_project_id_project"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project_image")),
    )
    op.create_index(
        op.f("ix_project_image_project_id"), "project_image", ["project_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_project_image_project_id"), table_name="project_image")
    op.drop_table("project_image")
    op.drop_index(op.f("ix_visit_created_at"), table_name="visit")
    op.drop_table("visit")
    op.drop_table("skill")
    op.drop_table("project")
    op.drop_table("profile")
    op.drop_table("experience")
    op.drop_table("contact_message")
