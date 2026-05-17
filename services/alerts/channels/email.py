import aiosmtplib
from email.message import EmailMessage

from config.settings import get_settings
from shared.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


async def send_email_alert(title: str, message: str, severity: str) -> bool:
    if not settings.smtp_user:
        logger.warning("smtp_not_configured")
        return False

    msg = EmailMessage()
    msg["Subject"] = f"[{severity.upper()}] BankOps Alert: {title}"
    msg["From"] = settings.alert_email_from
    msg["To"] = settings.alert_email_to
    msg.set_content(message)

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
        )
        logger.info("email_alert_sent", title=title, to=settings.alert_email_to)
        return True
    except Exception as exc:
        logger.error("email_alert_failed", error=str(exc), title=title)
        return False
