import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from models.alert import AlertStatus
from repositories.alert_repository import AlertRepository
from services.alerts.channels.slack import send_slack_alert
from services.alerts.channels.email import send_email_alert
from shared.logging import get_logger

logger = get_logger(__name__)


class AlertDispatcher:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.alert_repo = AlertRepository(session)

    async def dispatch_pending(self) -> int:
        """Dispatch all unsent open alerts through configured channels."""
        alerts = await self.alert_repo.list(status=AlertStatus.OPEN, limit=100)
        dispatched = 0

        for alert in alerts:
            if not alert.slack_sent:
                sent = await send_slack_alert(alert.title, alert.message, alert.severity)
                if sent:
                    await self.alert_repo.mark_slack_sent(alert.id)

            if not alert.email_sent:
                sent = await send_email_alert(alert.title, alert.message, alert.severity)
                if sent:
                    await self.alert_repo.mark_email_sent(alert.id)

            dispatched += 1

        return dispatched
