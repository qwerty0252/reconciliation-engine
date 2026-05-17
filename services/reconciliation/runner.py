import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from services.reconciliation.engine import ReconciliationEngine
from repositories.reconciliation_repository import ReconciliationRepository
from models.reconciliation_run import ReconciliationMode
from shared.logging import get_logger

logger = get_logger(__name__)


async def run_reconciliation(
    session: AsyncSession,
    mode: ReconciliationMode,
    run_id: uuid.UUID | None = None,
) -> uuid.UUID:
    recon_repo = ReconciliationRepository(session)
    engine = ReconciliationEngine(session)

    if run_id is None:
        run = await recon_repo.create_run(mode)
        run_id = run.id

    logger.info("reconciliation_run_started", run_id=str(run_id), mode=mode)

    try:
        if mode == ReconciliationMode.RECORD_TO_RECORD:
            await engine.run_record_to_record(run_id)
        elif mode == ReconciliationMode.SETTLEMENT:
            await engine.run_settlement_reconciliation(run_id)
        elif mode == ReconciliationMode.REVERSAL:
            await engine.run_reversal_reconciliation(run_id)
    except Exception as exc:
        await recon_repo.fail_run(run_id, str(exc))
        logger.error(
            "reconciliation_run_failed", run_id=str(run_id), error=str(exc)
        )
        raise

    return run_id
