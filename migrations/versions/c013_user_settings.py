"""user settings, privacy, password_changed_at

Revision ID: c013_user_settings
Revises: c012_seed_kopilka
Create Date: 2026-04-23 22:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c013_user_settings"
down_revision: Union[str, None] = "c012_seed_kopilka"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("timezone", sa.String(50), nullable=False, server_default="Europe/Moscow"))
    op.add_column("users", sa.Column("location", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("notify_new_sets", sa.Boolean, nullable=False, server_default="true"))
    op.add_column("users", sa.Column("notify_author_articles", sa.Boolean, nullable=False, server_default="true"))
    op.add_column("users", sa.Column("notify_subscriptions", sa.Boolean, nullable=False, server_default="true"))
    op.add_column("users", sa.Column("notify_set_changes", sa.Boolean, nullable=False, server_default="true"))
    op.add_column("users", sa.Column("notify_reminders", sa.Boolean, nullable=False, server_default="true"))
    op.add_column("users", sa.Column("privacy_sets", sa.String(20), nullable=False, server_default="all"))
    op.add_column("users", sa.Column("privacy_articles", sa.String(20), nullable=False, server_default="all"))
    op.add_column("users", sa.Column("privacy_profile", sa.String(20), nullable=False, server_default="all"))
    op.add_column("notifications", sa.Column("action_status", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("notifications", "action_status")
    op.drop_column("users", "privacy_profile")
    op.drop_column("users", "privacy_articles")
    op.drop_column("users", "privacy_sets")
    op.drop_column("users", "notify_reminders")
    op.drop_column("users", "notify_set_changes")
    op.drop_column("users", "notify_subscriptions")
    op.drop_column("users", "notify_author_articles")
    op.drop_column("users", "notify_new_sets")
    op.drop_column("users", "password_changed_at")
    op.drop_column("users", "location")
    op.drop_column("users", "timezone")
