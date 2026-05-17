import httpx

from config.settings import get_settings
from shared.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


async def send_slack_alert(title: str, message: str, severity: str) -> bool:
    if not settings.slack_webhook_url:
        logger.warning("slack_webhook_not_configured")
        return False

    colour_map = {"info": "#36a64f", "warning": "#ffcc00", "critical": "#ff0000"}
    colour = colour_map.get(severity.lower(), "#cccccc")

    payload = {
        "attachments": [
            {
                "color": colour,
                "title": f"[{severity.upper()}] {title}",
                "text": message,
                "footer": "BankOps Reconciliation Engine",
            }
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(settings.slack_webhook_url, json=payload)
            response.raise_for_status()
            logger.info("slack_alert_sent", title=title, severity=severity)
            return True
    except Exception as exc:
        logger.error("slack_alert_failed", error=str(exc), title=title)
        return False
