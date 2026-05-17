import uuid
from datetime import datetime

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.alert import Alert, AlertStatus, AlertSeverity, AlertType


class AlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: dict) -> Alert:
        alert = Alert(**data)
        self.session.add(alert)
        await self.session.commit()
        await self.session.refresh(alert)
        return alert

    async def get_by_id(self, alert_id: uuid.UUID) -> Alert | None:
        result = await self.session.execute(
            select(Alert).where(Alert.id == alert_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        severity: AlertSeverity | None = None,
        status: AlertStatus | None = None,
        alert_type: AlertType | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Alert]:
        q = select(Alert)
        if severity:
            q = q.where(Alert.severity == severity.value)
        if status:
            q = q.where(Alert.status == status.value)
        if alert_type:
            q = q.where(Alert.alert_type == alert_type.value)
        q = q.order_by(Alert.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def acknowledge(self, alert_id: uuid.UUID) -> Alert | None:
        await self.session.execute(
            update(Alert)
            .where(Alert.id == alert_id)
            .values(
                status=AlertStatus.ACKNOWLEDGED.value,
                acknowledged_at=func.now(),
            )
        )
        await self.session.commit()
        return await self.get_by_id(alert_id)

    async def mark_email_sent(self, alert_id: uuid.UUID) -> None:
        await self.session.execute(
            update(Alert).where(Alert.id == alert_id).values(email_sent=True)
        )
        await self.session.commit()

    async def mark_slack_sent(self, alert_id: uuid.UUID) -> None:
        await self.session.execute(
            update(Alert).where(Alert.id == alert_id).values(slack_sent=True)
        )
        await self.session.commit()

    async def count_open_by_severity(self) -> dict[str, int]:
        result = await self.session.execute(
            select(Alert.severity, func.count())
            .where(Alert.status == AlertStatus.OPEN.value)
            .group_by(Alert.severity)
        )
        return {row[0]: row[1] for row in result.all()}

    async def open_types(self) -> set:
        """Return the set of alert_type values that currently have an open alert."""
        result = await self.session.execute(
            select(Alert.alert_type).where(Alert.status == AlertStatus.OPEN.value)
        )
        return {row[0] for row in result.all()}
