"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-27 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("language_code", sa.String(length=16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_table(
        "genres",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("external_id", sa.Integer(), nullable=False),
        sa.Column("media_type", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source",
            "external_id",
            "media_type",
            name="uq_genres_source_external_media_type",
        ),
    )

    op.create_table(
        "media_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("external_id", sa.Integer(), nullable=False),
        sa.Column("imdb_id", sa.String(length=32), nullable=True),
        sa.Column("media_type", sa.String(length=16), nullable=False),
        sa.Column("original_title", sa.String(length=512), nullable=True),
        sa.Column("original_language", sa.String(length=16), nullable=True),
        sa.Column("release_year", sa.Integer(), nullable=True),
        sa.Column("poster_path", sa.String(length=512), nullable=True),
        sa.Column("backdrop_path", sa.String(length=512), nullable=True),
        sa.Column("runtime_minutes", sa.Integer(), nullable=True),
        sa.Column("tmdb_rating", sa.Float(), nullable=True),
        sa.Column("tmdb_vote_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source",
            "external_id",
            "media_type",
            name="uq_media_items_source_external_media_type",
        ),
    )

    op.create_table(
        "media_genres",
        sa.Column("media_id", sa.Integer(), nullable=False),
        sa.Column("genre_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["genre_id"], ["genres.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["media_id"], ["media_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("media_id", "genre_id"),
    )

    op.create_table(
        "media_translations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("media_id", sa.Integer(), nullable=False),
        sa.Column("language_code", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("overview", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["media_id"], ["media_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("media_id", "language_code", name="uq_media_translations_media_language"),
    )

    op.create_table(
        "soundtracks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("media_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("artist", sa.String(length=512), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("external_url", sa.String(length=2048), nullable=False),
        sa.Column("preview_url", sa.String(length=2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["media_id"], ["media_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_soundtracks_media_id"), "soundtracks", ["media_id"], unique=False)

    op.create_table(
        "user_genres",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("genre_id", sa.Integer(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["genre_id"], ["genres.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "genre_id"),
    )

    op.create_table(
        "user_media",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("media_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("rated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("temporary_hidden_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "rating IS NULL OR (rating >= 1 AND rating <= 10)",
            name="ck_user_media_rating_range",
        ),
        sa.CheckConstraint(
            "status IN ('wishlist', 'watched', 'hidden', 'ignored')",
            name="ck_user_media_status",
        ),
        sa.ForeignKeyConstraint(["media_id"], ["media_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "media_id"),
    )
    op.create_index(op.f("ix_user_media_status"), "user_media", ["status"], unique=False)

    op.create_table(
        "user_mood_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(length=16), nullable=False),
        sa.Column("mood_tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("max_runtime_minutes", sa.Integer(), nullable=True),
        sa.Column("company_type", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "content_type IN ('movie', 'tv', 'any')",
            name="ck_user_mood_sessions_content_type",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_mood_sessions_user_id"), "user_mood_sessions", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_mood_sessions_user_id"), table_name="user_mood_sessions")
    op.drop_table("user_mood_sessions")
    op.drop_index(op.f("ix_user_media_status"), table_name="user_media")
    op.drop_table("user_media")
    op.drop_table("user_genres")
    op.drop_index(op.f("ix_soundtracks_media_id"), table_name="soundtracks")
    op.drop_table("soundtracks")
    op.drop_table("media_translations")
    op.drop_table("media_genres")
    op.drop_table("media_items")
    op.drop_table("genres")
    op.drop_table("users")
