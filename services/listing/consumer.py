import json
from aio_pika.abc import AbstractIncomingMessage
import aio_pika
from typing import cast
from database import engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from models import Auction

async def handle_bid_placed(
    message: AbstractIncomingMessage
) -> None:
    msg = cast(aio_pika.IncomingMessage, message)

    async with msg.process():
        await on_bid_placed(msg.body)

async def on_bid_placed(body: bytes):
    data = json.loads(body)

    async with AsyncSession(engine) as db:
        stmt = (
            update(Auction)
            .where(
                Auction.id == data["auction_id"],
                Auction.version == data["version"] - 1
            )
            .values(
                current_price=data["amount"],
                current_bidder_id=data["bidder_id"],
                version=data["version"]
            )
            .returning(Auction.id)
        )

        result = await db.execute(stmt)

    updated_id = result.scalar_one_or_none()

    if updated_id is None:
        print("Stale or out-of-order event")
        await db.rollback()
        return

    await db.commit()