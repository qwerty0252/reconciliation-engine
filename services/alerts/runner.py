import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from shared.database import AsyncSessionLocal, create_tables
from shared.logging import configure_logging, get_logger
from services.alerts.engine import AlertEngine
from services.alerts.dispatcher import AlertDispatcher

logger = get_logger(__name__)


async def evaluate_and_dispatch() -> None:
    async with AsyncSessionLocal() as session:
        engine = AlertEngine(session)
        await engine.evaluate_mismatches()

        dispatcher = AlertDispatcher(session)
        dispatched = await dispatcher.dispatch_pending()
        if dispatched:
            logger.info("alerts_dispatched", count=dispatched)


async def main() -> None:
    configure_logging()
    await create_tables()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        evaluate_and_dispatch,
        trigger=IntervalTrigger(seconds=30),
        id="alert_evaluator",
        name="Alert Evaluation & Dispatch",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("alerts_service_started")

    try:
        await asyncio.Future()
    except (asyncio.CancelledError, KeyboardInterrupt):
        scheduler.shutdown()
        logger.info("alerts_service_stopped")


if __name__ == "__main__":
    asyncio.run(main())
