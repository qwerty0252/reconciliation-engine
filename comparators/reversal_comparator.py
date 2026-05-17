from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

from models.transaction import Transaction
from models.mismatch import MismatchType
from config.settings import get_settings

settings = get_settings()


@dataclass
class ReversalResult:
    has_mismatch: bool
    mismatch_type: MismatchType | None
    description: str
    details: dict


class ReversalComparator:
    """Validate reversal correctness and timing."""

    def check_delayed_reversal(
        self, reversal: Transaction, original: Transaction | None
    ) -> ReversalResult:
        if original is None:
            return ReversalResult(
                has_mismatch=True,
                mismatch_type=MismatchType.ORPHAN_REVERSAL,
                description=(
                    f"Orphan reversal detected: {reversal.transaction_id} "
                    f"references {reversal.reversal_reference} which does not exist"
                ),
                details={
                    "reversal_id": reversal.transaction_id,
                    "reversal_reference": reversal.reversal_reference,
                    "source_system": reversal.source_system,
                },
            )

        threshold = timedelta(hours=settings.recon_reversal_delay_hours)
        delay = reversal.timestamp.replace(tzinfo=timezone.utc) - original.timestamp.replace(
            tzinfo=timezone.utc
        )

        if delay > threshold:
            return ReversalResult(
                has_mismatch=True,
                mismatch_type=MismatchType.DELAYED_REVERSAL,
                description=(
                    f"Delayed reversal for transaction {original.transaction_id}: "
                    f"reversed after {delay.total_seconds() / 3600:.1f} hours "
                    f"(threshold: {settings.recon_reversal_delay_hours}h)"
                ),
                details={
                    "original_id": original.transaction_id,
                    "reversal_id": reversal.transaction_id,
                    "delay_hours": round(delay.total_seconds() / 3600, 2),
                    "threshold_hours": settings.recon_reversal_delay_hours,
                },
            )

        return ReversalResult(
            has_mismatch=False, mismatch_type=None, description="", details={}
        )
