import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from shared.database import AsyncSessionLocal, create_tables
from shared.logging import configure_logging, get_logger
from services.reconciliation.runner import run_reconciliation
from models.reconciliation_run import ReconciliationMode
from config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


async def scheduled_record_to_record() -> None:
    async with AsyncSessionLocal() as session:
        await run_reconciliation(session, ReconciliationMode.RECORD_TO_RECORD)


async def scheduled_settlement() -> None:
    async with AsyncSessionLocal() as session:
        await run_reconciliation(session, ReconciliationMode.SETTLEMENT)


async def scheduled_reversal() -> None:
    async with AsyncSessionLocal() as session:
        await run_reconciliation(session, ReconciliationMode.REVERSAL)


async def main() -> None:
    configure_logging()
    await create_tables()

    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        scheduled_record_to_record,
        trigger=IntervalTrigger(minutes=settings.recon_schedule_minutes),
        id="record_to_record",
        name="Record-to-Record Reconciliation",
        replace_existing=True,
    )
    scheduler.add_job(
        scheduled_settlement,
        trigger=IntervalTrigger(hours=1),
        id="settlement_recon",
        name="Settlement Reconciliation",
        replace_existing=True,
    )
    scheduler.add_job(
        scheduled_reversal,
        trigger=IntervalTrigger(hours=1),
        id="reversal_recon",
        name="Reversal Reconciliation",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        "reconciliation_scheduler_started",
        record_to_record_interval_minutes=settings.recon_schedule_minutes,
    )

    try:
        await asyncio.Future()
    except (asyncio.CancelledError, KeyboardInterrupt):
        scheduler.shutdown()
        logger.info("reconciliation_scheduler_stopped")


if __name__ == "__main__":
    asyncio.run(main())
