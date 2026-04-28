"""notifications rework: new columns + messages table + seed data

Revision ID: c018_notifications_rework
Revises: c017_deposit_tariff
Create Date: 2026-04-27 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c018_notifications_rework"
down_revision: Union[str, None] = "c017_deposit_tariff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column("author_id", sa.UUID(), nullable=True))
    op.add_column("notifications", sa.Column("direction", sa.String(20), nullable=True))
    op.add_column("notifications", sa.Column("set_id", sa.String(20), nullable=True))
    op.add_column("notifications", sa.Column("set_title", sa.String(200), nullable=True))
    op.add_column("notifications", sa.Column("article_id", sa.String(20), nullable=True))
    op.add_column("notifications", sa.Column("article_title", sa.String(300), nullable=True))
    op.add_column(
        "notifications",
        sa.Column("messages_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_foreign_key(
        "fk_notifications_author_id",
        "notifications",
        "users",
        ["author_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "notification_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("notification_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["notification_id"],
            ["notifications.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
    )
    op.create_index(
        "ix_notification_messages_notification_id",
        "notification_messages",
        ["notification_id"],
    )

    conn = op.get_bind()

    row = conn.execute(sa.text("SELECT id FROM users ORDER BY created_at ASC LIMIT 1")).fetchone()
    if row is None:
        return
    uid = str(row[0])

    conn.execute(
        sa.text(
            """
            INSERT INTO notifications
                (user_id, type, title, description, is_read, direction, messages_count)
            VALUES
                (:uid, 'system', 'Добро пожаловать в SmartSpend!',
                 'Мы рады видеть вас. Настройте профиль и начните управлять финансами.',
                 false, NULL, 0)
            ON CONFLICT DO NOTHING
            """
        ),
        {"uid": uid},
    )

    conn.execute(
        sa.text(
            """
            INSERT INTO notifications
                (user_id, type, title, description, is_read, author_id, direction, messages_count)
            VALUES
                (:uid, 'subscription', 'Новый набор от автора',
                 'Автор, на которого вы подписаны, опубликовал новый набор.',
                 false, :uid, NULL, 0),
                (:uid, 'subscription', 'Обновление набора',
                 'Набор, который вы добавили, был обновлён автором.',
                 true, :uid, NULL, 0)
            ON CONFLICT DO NOTHING
            """
        ),
        {"uid": uid},
    )

    conn.execute(
        sa.text(
            """
            INSERT INTO notifications
                (user_id, type, title, description, is_read, author_id, direction, messages_count)
            VALUES
                (:uid, 'reply', 'Ответ на ваш комментарий',
                 'Пользователь ответил на ваш комментарий к набору.',
                 false, :uid, NULL, 0)
            ON CONFLICT DO NOTHING
            """
        ),
        {"uid": uid},
    )

    conn.execute(
        sa.text(
            """
            INSERT INTO notifications
                (user_id, type, title, description, is_read, direction, messages_count)
            VALUES
                (:uid, 'reminder', 'Пора пополнить запасы',
                 'Некоторые расходники скоро закончатся. Проверьте инвентарь.',
                 false, NULL, 0)
            ON CONFLICT DO NOTHING
            """
        ),
        {"uid": uid},
    )

    conn.execute(
        sa.text(
            """
            INSERT INTO notifications
                (user_id, type, title, description, is_read, author_id,
                 direction, action_status, set_id, set_title, messages_count)
            VALUES
                (:uid, 'request', 'Запрос на добавление набора',
                 'Пользователь просит добавить его набор в каталог.',
                 false, :uid, 'incoming', 'pending', NULL, NULL, 0),
                (:uid, 'request', 'Ваш запрос на публикацию',
                 'Вы отправили запрос на публикацию набора в каталог.',
                 true, :uid, 'outgoing', 'approved', NULL, NULL, 1),
                (:uid, 'request', 'Запрос на редактирование статьи',
                 'Пользователь просит внести правки в статью.',
                 false, :uid, 'incoming', 'rejected', NULL, NULL, 2)
            ON CONFLICT DO NOTHING
            """
        ),
        {"uid": uid},
    )


def downgrade() -> None:
    op.drop_index("ix_notification_messages_notification_id", table_name="notification_messages")
    op.drop_table("notification_messages")
    op.drop_constraint("fk_notifications_author_id", "notifications", type_="foreignkey")
    op.drop_column("notifications", "messages_count")
    op.drop_column("notifications", "article_title")
    op.drop_column("notifications", "article_id")
    op.drop_column("notifications", "set_title")
    op.drop_column("notifications", "set_id")
    op.drop_column("notifications", "direction")
    op.drop_column("notifications", "author_id")
