"""fill set/article in test notifications + add messages

Revision ID: c019_fix_notif_seed
Revises: c018_notifications_rework
Create Date: 2026-04-29 11:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c019_fix_notif_seed"
down_revision: Union[str, None] = "c018_notifications_rework"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    sets = conn.execute(sa.text("SELECT id, title FROM sets LIMIT 3")).fetchall()
    arts = conn.execute(sa.text("SELECT id, title FROM articles LIMIT 3")).fetchall()
    uid_row = conn.execute(sa.text("SELECT id FROM users ORDER BY created_at ASC LIMIT 1")).fetchone()

    if not uid_row:
        return

    uid = str(uid_row[0])
    reqs = conn.execute(
        sa.text("SELECT id FROM notifications WHERE type = 'request' ORDER BY id ASC")
    ).fetchall()

    for i, req in enumerate(reqs):
        nid = req[0]
        s = sets[i] if i < len(sets) else (sets[0] if sets else None)
        a = arts[i] if i < len(arts) else (arts[0] if arts else None)
        conn.execute(
            sa.text(
                "UPDATE notifications SET set_id = :sid, set_title = :stitle, "
                "article_id = :aid, article_title = :atitle WHERE id = :nid"
            ),
            {
                "sid": s[0] if s else None,
                "stitle": s[1] if s else None,
                "aid": a[0] if a else None,
                "atitle": a[1] if a else None,
                "nid": nid,
            },
        )

        conn.execute(
            sa.text(
                "INSERT INTO notification_messages (notification_id, user_id, text) "
                "VALUES (:nid, :uid, :text)"
            ),
            {"nid": nid, "uid": uid, "text": "Добрый день, хочу предложить рассмотреть мою статью к набору"},
        )

        if i > 0:
            conn.execute(
                sa.text(
                    "INSERT INTO notification_messages (notification_id, user_id, text) "
                    "VALUES (:nid, :uid, :text)"
                ),
                {"nid": nid, "uid": uid, "text": "Спасибо, посмотрю в ближайшее время"},
            )

    conn.execute(
        sa.text(
            "UPDATE notifications SET messages_count = ("
            "SELECT count(*) FROM notification_messages WHERE notification_messages.notification_id = notifications.id"
            ") WHERE type = 'request'"
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM notification_messages"))
    conn.execute(
        sa.text(
            "UPDATE notifications SET set_id = NULL, set_title = NULL, "
            "article_id = NULL, article_title = NULL, messages_count = 0 "
            "WHERE type = 'request'"
        )
    )
