from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from repositories.transaction_repository import TransactionRepository
from repositories.mismatch_repository import MismatchRepository
from repositories.reconciliation_repository import ReconciliationRepository
from repositories.alert_repository import AlertRepository
from models.mismatch import MismatchStatus
from models.reconciliation_run import ReconciliationStatus

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
async def dashboard_summary(session: AsyncSession = Depends(get_db)):
    txn_repo = TransactionRepository(session)
    mismatch_repo = MismatchRepository(session)
    recon_repo = ReconciliationRepository(session)
    alert_repo = AlertRepository(session)

    total_transactions = await txn_repo.total_count()
    open_mismatches = await mismatch_repo.count_open()
    mismatch_by_type = await mismatch_repo.count_by_type()
    alert_by_severity = await alert_repo.count_open_by_severity()

    runs = await recon_repo.list_runs(limit=100)
    completed = [r for r in runs if r.status == ReconciliationStatus.COMPLETED]

    total_mismatches = sum(mismatch_by_type.values())
    reconciled = max(0, total_transactions - total_mismatches)
    success_rate = (
        round(reconciled / total_transactions * 100, 1) if total_transactions > 0 else 0.0
    )

    return {
        "total_transactions": total_transactions,
        "reconciled_transactions": reconciled,
        "unreconciled_transactions": total_mismatches,
        "open_mismatches": open_mismatches,
        "mismatch_count_by_type": mismatch_by_type,
        "reconciliation_success_rate_pct": success_rate,
        "open_alerts_by_severity": alert_by_severity,
        "total_reconciliation_runs": len(runs),
        "completed_reconciliation_runs": len(completed),
    }
