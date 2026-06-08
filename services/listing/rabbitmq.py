import aio_pika
from aio_pika.abc import AbstractExchange
import os

RABBITMQ_URL = os.getenv('RABBITMQ_URL', '')

exchange: AbstractExchange | None = None

async def get_connection():
    print(RABBITMQ_URL)
    return await aio_pika.connect_robust(RABBITMQ_URL)
