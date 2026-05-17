from dataclasses import dataclass
from datetime import datetime, timezone
from datetime import timedelta

from models.transaction import Transaction
from models.mismatch import MismatchType
from config.settings import get_settings

settings = get_settings()


@dataclass
class SettlementResult:
    has_mismatch: bool
    mismatch_type: MismatchType | None
    description: str
    details: dict


class SettlementComparator:
    """Compare settlement records against transaction records."""

    def check_settlement_delay(self, transaction: Transaction) -> SettlementResult:
        if transaction.settlement_id:
            return SettlementResult(
                has_mismatch=False, mismatch_type=None, description="", details={}
            )

        threshold = timedelta(hours=settings.recon_settlement_delay_hours)
        age = datetime.now(tz=timezone.utc) - transaction.timestamp.replace(
            tzinfo=timezone.utc
        )

        if age > threshold and transaction.status.upper() == "SUCCESS":
            return SettlementResult(
                has_mismatch=True,
                mismatch_type=MismatchType.SETTLEMENT_DELAY,
                description=(
                    f"Settlement delay detected for transaction {transaction.transaction_id}: "
                    f"unsettled for {age.total_seconds() / 3600:.1f} hours "
                    f"(threshold: {settings.recon_settlement_delay_hours}h)"
                ),
                details={
                    "transaction_id": transaction.transaction_id,
                    "source_system": transaction.source_system,
                    "age_hours": round(age.total_seconds() / 3600, 2),
                    "threshold_hours": settings.recon_settlement_delay_hours,
                },
            )

        return SettlementResult(
            has_mismatch=False, mismatch_type=None, description="", details={}
        )
