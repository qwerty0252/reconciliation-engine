from sqlalchemy.ext.asyncio import AsyncSession

from models.alert import AlertType, AlertSeverity
from models.mismatch import MismatchType, MismatchStatus
from repositories.mismatch_repository import MismatchRepository
from repositories.alert_repository import AlertRepository
from shared.logging import get_logger

logger = get_logger(__name__)

MISMATCH_ALERT_THRESHOLD = 5
DUPLICATE_SPIKE_THRESHOLD = 3


class AlertEngine:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.mismatch_repo = MismatchRepository(session)
        self.alert_repo = AlertRepository(session)

    async def evaluate_mismatches(self) -> list[dict]:
        """Evaluate open mismatches and generate alerts where thresholds are exceeded."""
        counts = await self.mismatch_repo.count_by_type()
        existing_open_types = await self.alert_repo.open_types()
        alerts_to_create: list[dict] = []

        total_open = sum(counts.values())

        if total_open >= MISMATCH_ALERT_THRESHOLD and AlertType.HIGH_MISMATCH_VOLUME not in existing_open_types:
            breakdown = ", ".join(f"{k.value}: {v}" for k, v in counts.items())
            alerts_to_create.append({
                "alert_type": AlertType.HIGH_MISMATCH_VOLUME,
                "severity": AlertSeverity.CRITICAL if total_open > 20 else AlertSeverity.WARNING,
                "title": "High Mismatch Volume Detected",
                "message": (
                    f"{total_open} open mismatches detected across all reconciliation runs. "
                    f"Breakdown: {breakdown}"
                ),
            })

        dup_count = counts.get(MismatchType.DUPLICATE_TRANSACTION, 0)
        if dup_count >= DUPLICATE_SPIKE_THRESHOLD and AlertType.DUPLICATE_SPIKE not in existing_open_types:
            alerts_to_create.append({
                "alert_type": AlertType.DUPLICATE_SPIKE,
                "severity": AlertSeverity.WARNING,
                "title": "Duplicate Transaction Spike",
                "message": f"{dup_count} duplicate transactions detected.",
            })

        settlement_count = counts.get(MismatchType.SETTLEMENT_DELAY, 0)
        if settlement_count > 0 and AlertType.SETTLEMENT_DELAY not in existing_open_types:
            alerts_to_create.append({
                "alert_type": AlertType.SETTLEMENT_DELAY,
                "severity": AlertSeverity.CRITICAL,
                "title": "Settlement Delays Detected",
                "message": f"{settlement_count} transactions have exceeded settlement SLA.",
            })

        missing_count = counts.get(MismatchType.MISSING_TRANSACTION, 0)
        if missing_count >= MISMATCH_ALERT_THRESHOLD and AlertType.MISSING_TRANSACTION_SPIKE not in existing_open_types:
            alerts_to_create.append({
                "alert_type": AlertType.MISSING_TRANSACTION_SPIKE,
                "severity": AlertSeverity.CRITICAL,
                "title": "Missing Transaction Spike",
                "message": f"{missing_count} missing transactions detected across systems.",
            })

        created = []
        for alert_data in alerts_to_create:
            alert = await self.alert_repo.create(alert_data)
            created.append(alert)
            logger.info(
                "alert_created",
                alert_type=alert.alert_type,
                severity=alert.severity,
                id=str(alert.id),
            )

        return created

    async def evaluate_recon_failure(self, run_id: str, error: str) -> None:
        await self.alert_repo.create({
            "alert_type": AlertType.RECONCILIATION_JOB_FAILURE,
            "severity": AlertSeverity.CRITICAL,
            "title": "Reconciliation Job Failed",
            "message": f"Reconciliation run {run_id} failed: {error}",
        })
