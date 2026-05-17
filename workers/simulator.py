"""
BankOps Transaction Simulator
Publishes synthetic transaction events to RabbitMQ for testing/demo purposes.

Usage:
    python -m workers.simulator --count 100 --source gateway
    python -m workers.simulator --mode batch --count 500
"""
import asyncio
import json
import random
import uuid
import argparse
from datetime import datetime, timezone, timedelta

from shared.rabbitmq import get_channel, declare_exchange, close
from shared.logging import configure_logging, get_logger
import aio_pika

logger = get_logger(__name__)

SOURCES = ["gateway", "switch", "ledger"]
STATUSES = ["SUCCESS", "FAILED", "PENDING", "REVERSAL"]
CURRENCIES = ["NGN", "USD", "GBP", "EUR"]
STATUS_WEIGHTS = [0.75, 0.10, 0.10, 0.05]


def generate_transaction(
    source: str | None = None,
    reference: str | None = None,
    amount: float | None = None,
    status: str | None = None,
) -> dict:
    ref = reference or f"REF_{uuid.uuid4().hex[:8].upper()}"
    ts = datetime.now(tz=timezone.utc) - timedelta(
        minutes=random.randint(0, 60 * 24 * 7)
    )
    return {
        "transaction_id": f"TXN_{uuid.uuid4().hex[:10].upper()}",
        "reference": ref,
        "amount": amount or round(random.uniform(100, 1_000_000), 2),
        "currency": random.choice(CURRENCIES),
        "status": status or random.choices(STATUSES, weights=STATUS_WEIGHTS)[0],
        "source_system": source or random.choice(SOURCES),
        "timestamp": ts.isoformat(),
    }


async def simulate(count: int, source: str | None, delay_ms: int) -> None:
    configure_logging()
    channel = await get_channel()
    exchange = await declare_exchange(channel)

    logger.info("simulator_starting", count=count, source=source or "random")

    for i in range(count):
        payload = generate_transaction(source=source)
        body = json.dumps(payload).encode()
        await exchange.publish(
            aio_pika.Message(body=body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
            routing_key="transaction.ingest",
        )
        if (i + 1) % 50 == 0:
            logger.info("simulator_progress", sent=i + 1, total=count)
        if delay_ms > 0:
            await asyncio.sleep(delay_ms / 1000)

    logger.info("simulator_done", total_sent=count)
    await close()


def main() -> None:
    parser = argparse.ArgumentParser(description="BankOps Transaction Simulator")
    parser.add_argument("--count", type=int, default=100, help="Number of events to publish")
    parser.add_argument("--source", type=str, default=None, help="Source system override")
    parser.add_argument("--delay-ms", type=int, default=0, help="Delay between events (ms)")
    args = parser.parse_args()
    asyncio.run(simulate(args.count, args.source, args.delay_ms))


if __name__ == "__main__":
    main()
