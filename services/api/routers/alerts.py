import uuid

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from repositories.alert_repository import AlertRepository
from models.alert import AlertSeverity, AlertStatus, AlertType

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("")
async def list_alerts(
    severity: AlertSeverity | None = Query(default=None),
    alert_status: AlertStatus | None = Query(default=None, alias="status"),
    alert_type: AlertType | None = Query(default=None),
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
):
    repo = AlertRepository(session)
    alerts = await repo.list(
        severity=severity,
        status=alert_status,
        alert_type=alert_type,
        limit=limit,
        offset=offset,
    )
    return {
        "data": [_serialize(a) for a in alerts],
        "limit": limit,
        "offset": offset,
    }


@router.get("/summary")
async def alert_summary(session: AsyncSession = Depends(get_db)):
    repo = AlertRepository(session)
    by_severity = await repo.count_open_by_severity()
    return {"open_by_severity": by_severity}


@router.get("/{alert_id}")
async def get_alert(alert_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    repo = AlertRepository(session)
    alert = await repo.get_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return _serialize(alert)


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: uuid.UUID, session: AsyncSession = Depends(get_db)
):
    repo = AlertRepository(session)
    alert = await repo.acknowledge(alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return _serialize(alert)


def _serialize(a) -> dict:
    return {
        "id": str(a.id),
        "alert_type": a.alert_type,
        "severity": a.severity,
        "status": a.status,
        "title": a.title,
        "message": a.message,
        "email_sent": a.email_sent,
        "slack_sent": a.slack_sent,
        "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
        "created_at": a.created_at.isoformat(),
    }
