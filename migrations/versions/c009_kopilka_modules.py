"""deposits, cards, companies, promos, whispers

Revision ID: c009_kopilka
Revises: c008_notes
Create Date: 2026-04-22 12:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c009_kopilka"
down_revision: Union[str, None] = "c008_notes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "deposits",
        sa.Column("id", sa.String(20), primary_key=True),
        sa.Column("bank_name", sa.String(100), nullable=False),
        sa.Column("bank_color", sa.String(7), nullable=False),
        sa.Column("bank_text_color", sa.String(7), nullable=False, server_default="#FFF"),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("rates", sa.dialects.postgresql.JSONB, nullable=False),
        sa.Column("min_amount", sa.Integer, nullable=True),
        sa.Column("max_amount", sa.Integer, nullable=True),
        sa.Column("replenishment", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("withdrawal", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("freq", sa.String(20), nullable=False, server_default="end"),
        sa.Column("is_systemic", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("conditions", sa.ARRAY(sa.Text), nullable=True),
        sa.Column("tags", sa.ARRAY(sa.Text), nullable=True),
        sa.Column("conditions_text", sa.Text, nullable=True),
        sa.Column("params", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "cards",
        sa.Column("id", sa.String(20), primary_key=True),
        sa.Column("bank_name", sa.String(100), nullable=False),
        sa.Column("bank_color", sa.String(7), nullable=False),
        sa.Column("bank_text_color", sa.String(7), nullable=False, server_default="#FFF"),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("card_type", sa.String(20), nullable=False),
        sa.Column("cashback", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("cashback_note", sa.Text, nullable=True),
        sa.Column("grace_days", sa.Integer, nullable=False, server_default="0"),
        sa.Column("fee", sa.Integer, nullable=False, server_default="0"),
        sa.Column("fee_base", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_systemic", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("conditions", sa.ARRAY(sa.Text), nullable=True),
        sa.Column("tags", sa.ARRAY(sa.Text), nullable=True),
        sa.Column("bonus_type", sa.String(50), nullable=True),
        sa.Column("bonus_system", sa.String(200), nullable=True),
        sa.Column("bonus_desc", sa.Text, nullable=True),
        sa.Column("fee_desc", sa.Text, nullable=True),
        sa.Column("url", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "companies",
        sa.Column("id", sa.String(30), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("abbr", sa.String(5), nullable=True),
        sa.Column("color", sa.String(7), nullable=False, server_default="#888"),
        sa.Column("category_id", sa.String(20), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("promo_types", sa.ARRAY(sa.Text), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "user_companies",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("company_id", sa.String(30), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "company_id", name="uq_user_company"),
    )

    op.create_table(
        "promos",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("company_id", sa.String(30), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category_id", sa.String(20), nullable=True),
        sa.Column("author_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("channel", sa.String(50), nullable=True),
        sa.Column("url", sa.Text, nullable=True),
        sa.Column("conditions", sa.ARRAY(sa.Text), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("votes_up", sa.Integer, nullable=False, server_default="0"),
        sa.Column("votes_down", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "promo_votes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("promo_id", sa.Integer, sa.ForeignKey("promos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vote", sa.String(10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "promo_id", name="uq_promo_vote"),
    )

    op.create_table(
        "promo_comments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("promo_id", sa.Integer, sa.ForeignKey("promos.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("initials", sa.String(2), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("parent_id", sa.Integer, sa.ForeignKey("promo_comments.id", ondelete="CASCADE"), nullable=True),
        sa.Column("likes_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("dislikes_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "user_cards",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("card_id", sa.String(20), sa.ForeignKey("cards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("spending", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "card_id", name="uq_user_card"),
    )


def downgrade() -> None:
    op.drop_table("user_cards")
    op.drop_table("promo_comments")
    op.drop_table("promo_votes")
    op.drop_table("promos")
    op.drop_table("user_companies")
    op.drop_table("companies")
    op.drop_table("cards")
    op.drop_table("deposits")
