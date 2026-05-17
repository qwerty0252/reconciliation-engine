import aio_pika
from aio_pika import ExchangeType
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel

from config.settings import get_settings

settings = get_settings()

_connection: AbstractRobustConnection | None = None
_channel: AbstractRobustChannel | None = None


async def get_connection() -> AbstractRobustConnection:
    global _connection
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    return _connection


async def get_channel() -> AbstractRobustChannel:
    global _channel
    connection = await get_connection()
    if _channel is None or _channel.is_closed:
        _channel = await connection.channel()
        await _channel.set_qos(prefetch_count=10)
    return _channel


async def declare_exchange(channel: AbstractRobustChannel) -> aio_pika.Exchange:
    return await channel.declare_exchange(
        settings.rabbitmq_exchange,
        ExchangeType.TOPIC,
        durable=True,
    )


async def declare_ingestion_queue(channel: AbstractRobustChannel) -> aio_pika.Queue:
    exchange = await declare_exchange(channel)
    queue = await channel.declare_queue(
        settings.rabbitmq_queue_ingestion,
        durable=True,
    )
    await queue.bind(exchange, routing_key="transaction.#")
    return queue


async def publish_message(routing_key: str, body: bytes) -> None:
    channel = await get_channel()
    exchange = await declare_exchange(channel)
    await exchange.publish(
        aio_pika.Message(body=body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
        routing_key=routing_key,
    )


async def close() -> None:
    global _connection, _channel
    if _channel and not _channel.is_closed:
        await _channel.close()
    if _connection and not _connection.is_closed:
        await _connection.close()
    _connection = None
    _channel = None
