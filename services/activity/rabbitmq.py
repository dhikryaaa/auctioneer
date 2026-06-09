import aio_pika
from aio_pika.abc import AbstractRobustConnection
from config import settings

_connection: AbstractRobustConnection | None = None

async def get_connection() -> AbstractRobustConnection:
    global _connection
    if _connection is None:
        _connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    return _connection

async def close_connection():
    if _connection:
        await _connection.close()