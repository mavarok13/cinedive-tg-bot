"""recommendation feed redesign

Revision ID: 0002_recommendation_feed
Revises: 0001_initial_schema
Create Date: 2026-07-02 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002_recommendation_feed"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("media_items", sa.Column("origin_country", sa.String(length=8), nullable=True))

    op.drop_constraint("ck_user_media_status", "user_media", type_="check")
    op.create_check_constraint(
        "ck_user_media_status",
        "user_media",
        "status IN ('shown', 'wishlist', 'watched', 'hidden', 'ignored')",
    )
    op.add_column("user_media", sa.Column("wishlist_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("user_media", sa.Column("watched_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("user_media", sa.Column("ignored_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("user_media", sa.Column("last_shown_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("user_media", sa.Column("last_interaction_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "user_media",
        sa.Column("shown_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.alter_column("user_media", "shown_count", server_default=None)

    op.create_table(
        "recommendation_queue_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("mood_session_id", sa.Integer(), nullable=False),
        sa.Column("media_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("bucket", sa.String(length=16), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("shown_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "bucket IN ('high', 'medium', 'exploration')",
            name="ck_recommendation_queue_bucket",
        ),
        sa.ForeignKeyConstraint(["media_id"], ["media_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["mood_session_id"], ["user_mood_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "mood_session_id",
            "media_id",
            name="uq_recommendation_queue_session_media",
        ),
        sa.UniqueConstraint(
            "mood_session_id",
            "position",
            name="uq_recommendation_queue_session_position",
        ),
    )
    op.create_index(
        op.f("ix_recommendation_queue_items_media_id"),
        "recommendation_queue_items",
        ["media_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_recommendation_queue_items_mood_session_id"),
        "recommendation_queue_items",
        ["mood_session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_recommendation_queue_items_user_id"),
        "recommendation_queue_items",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "user_preference_penalties",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("feature_type", sa.String(length=32), nullable=False),
        sa.Column("feature_value", sa.String(length=128), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "feature_type IN ('genre', 'origin_country', 'original_language', 'media_type')",
            name="ck_user_preference_penalties_feature_type",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "feature_type",
            "feature_value",
            name="uq_user_preference_penalty_feature",
        ),
    )
    op.create_index(
        op.f("ix_user_preference_penalties_expires_at"),
        "user_preference_penalties",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_preference_penalties_user_id"),
        "user_preference_penalties",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_preference_penalties_user_id"), table_name="user_preference_penalties")
    op.drop_index(op.f("ix_user_preference_penalties_expires_at"), table_name="user_preference_penalties")
    op.drop_table("user_preference_penalties")
    op.drop_index(op.f("ix_recommendation_queue_items_user_id"), table_name="recommendation_queue_items")
    op.drop_index(op.f("ix_recommendation_queue_items_mood_session_id"), table_name="recommendation_queue_items")
    op.drop_index(op.f("ix_recommendation_queue_items_media_id"), table_name="recommendation_queue_items")
    op.drop_table("recommendation_queue_items")

    op.drop_column("user_media", "shown_count")
    op.drop_column("user_media", "last_interaction_at")
    op.drop_column("user_media", "last_shown_at")
    op.drop_column("user_media", "ignored_at")
    op.drop_column("user_media", "watched_at")
    op.drop_column("user_media", "wishlist_at")
    op.drop_constraint("ck_user_media_status", "user_media", type_="check")
    op.create_check_constraint(
        "ck_user_media_status",
        "user_media",
        "status IN ('wishlist', 'watched', 'hidden', 'ignored')",
    )

    op.drop_column("media_items", "origin_country")
