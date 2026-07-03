"""recommendation discovery state

Revision ID: 0003_discovery_state
Revises: 0002_recommendation_feed
Create Date: 2026-07-03 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0003_discovery_state"
down_revision: str | None = "0002_recommendation_feed"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recommendation_discovery_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("mood_session_id", sa.Integer(), nullable=False),
        sa.Column("media_type", sa.String(length=16), nullable=False),
        sa.Column("sort_by", sa.String(length=64), nullable=False),
        sa.Column("genre_key", sa.String(length=256), nullable=False),
        sa.Column("filter_key", sa.String(length=256), nullable=False),
        sa.Column("next_page", sa.Integer(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("empty_result_count", sa.Integer(), nullable=False),
        sa.Column("exhausted", sa.Boolean(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "media_type IN ('movie', 'tv')",
            name="ck_recommendation_discovery_media_type",
        ),
        sa.ForeignKeyConstraint(["mood_session_id"], ["user_mood_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "mood_session_id",
            "media_type",
            "sort_by",
            "genre_key",
            "filter_key",
            name="uq_recommendation_discovery_strategy",
        ),
    )
    op.create_index(
        op.f("ix_recommendation_discovery_states_last_used_at"),
        "recommendation_discovery_states",
        ["last_used_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_recommendation_discovery_states_mood_session_id"),
        "recommendation_discovery_states",
        ["mood_session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_recommendation_discovery_states_user_id"),
        "recommendation_discovery_states",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_recommendation_discovery_states_user_id"), table_name="recommendation_discovery_states")
    op.drop_index(
        op.f("ix_recommendation_discovery_states_mood_session_id"),
        table_name="recommendation_discovery_states",
    )
    op.drop_index(
        op.f("ix_recommendation_discovery_states_last_used_at"),
        table_name="recommendation_discovery_states",
    )
    op.drop_table("recommendation_discovery_states")
