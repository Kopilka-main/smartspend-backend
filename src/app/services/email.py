import logging
from email.message import EmailMessage

import aiosmtplib

from src.app.core.config import settings

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, html: str) -> None:
    if not settings.smtp_host:
        logger.warning("SMTP not configured, skipping email to %s", to)
        return

    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(html, subtype="html")

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            use_tls=True,
        )
    except Exception:
        logger.exception("Failed to send email to %s", to)


async def send_verification_email(to: str, token: str) -> None:
    link = f"{settings.frontend_url}/#/verify-email?token={token}"
    html = (
        "<h2>Подтверждение email</h2>"
        f'<p>Для подтверждения email перейдите по ссылке:</p><p><a href="{link}">{link}</a></p>'
    )
    await send_email(to, "Подтверждение email — SmartSpend", html)


async def send_reset_password_email(to: str, token: str) -> None:
    link = f"{settings.frontend_url}/#/reset-password?token={token}"
    html = f'<h2>Сброс пароля</h2><p>Для сброса пароля перейдите по ссылке:</p><p><a href="{link}">{link}</a></p>'
    await send_email(to, "Сброс пароля — SmartSpend", html)
