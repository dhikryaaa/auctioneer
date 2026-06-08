import aio_pika
from aio_pika.abc import AbstractRobustConnection, AbstractExchange
from config import settings

_exchange: AbstractExchange | None = None
_connection: AbstractRobustConnection | None = None

async def init_rabbitmq():
    global _exchange, _connection
    _connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await _connection.channel()
    _exchange = await channel.declare_exchange(
        settings.EXCHANGE_NAME,
        aio_pika.ExchangeType.TOPIC,
        durable=True,
    )

def get_exchange() -> AbstractExchange:
    if _exchange is None:
        raise RuntimeError("RabbitMQ not initialised — call init_rabbitmq() on startup")
    return _exchange

async def close_rabbitmq():
    if _connection:
        await _connection.close()