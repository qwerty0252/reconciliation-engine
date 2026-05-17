import asyncio
import json

import aio_pika
from sqlalchemy.exc import IntegrityError

from shared.database import AsyncSessionLocal
from shared.rabbitmq import get_channel, declare_ingestion_queue
from shared.logging import get_logger, configure_logging
from services.ingestion.validator import TransactionEventSchema
from services.ingestion.normalizer import normalize
from repositories.transaction_repository import TransactionRepository

logger = get_logger(__name__)


async def handle_message(message: aio_pika.IncomingMessage) -> None:
    async with message.process(requeue=True):
        try:
            payload = json.loads(message.body)
            event = TransactionEventSchema(**payload)
            data = normalize(event)

            async with AsyncSessionLocal() as session:
                repo = TransactionRepository(session)
                existing = await repo.get_by_transaction_id_and_source(
                    event.transaction_id, event.source_system
                )
                if existing:
                    logger.info(
                        "duplicate_skipped",
                        transaction_id=event.transaction_id,
                        source_system=event.source_system,
                    )
                    return

                txn = await repo.create(data)
                logger.info(
                    "transaction_ingested",
                    id=str(txn.id),
                    transaction_id=txn.transaction_id,
                    source_system=txn.source_system,
                )
        except Exception as exc:
            logger.error("ingestion_error", error=str(exc), body=message.body[:200])
            raise


async def start_consumer() -> None:
    configure_logging()
    logger.info("ingestion_consumer_starting")

    channel = await get_channel()
    queue = await declare_ingestion_queue(channel)

    logger.info("waiting_for_messages", queue=queue.name)
    await queue.consume(handle_message)

    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        logger.info("ingestion_consumer_stopped")


if __name__ == "__main__":
    asyncio.run(start_consumer())
