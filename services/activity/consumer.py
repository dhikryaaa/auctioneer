import json
from datetime import datetime

import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from sqlalchemy import update
from sqlalchemy.dialects.sqlite import insert as upsert   # use postgresql dialect if you switch DBs

from config import settings
from database import SessionLocal as AsyncSessionLocal
from models import UserListing, UserBid
from rabbitmq import get_connection


async def start_consumer():
    connection = await get_connection()
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    exchange = await channel.declare_exchange(
        settings.EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
    )
    queue = await channel.declare_queue(settings.QUEUE_NAME, durable=True)
    for key in ("auction.created", "bid.placed", "auction.closed"):
        await queue.bind(exchange, routing_key=key)

    await queue.consume(handle_message)   # registers the callback, returns immediately


async def handle_message(message: AbstractIncomingMessage):
    async with message.process():   # ack on success, requeue if we raise
        data = json.loads(message.body)
        key = message.routing_key
        if key == "auction.created":
            await on_auction_created(data)
        elif key == "bid.placed":
            await on_bid_placed(data)
        elif key == "auction.closed":
            await on_auction_closed(data)


# ── auction.created → a new listing appears for the owner ────────────
async def on_auction_created(data: dict):
    async with AsyncSessionLocal() as db:
        stmt = (
            upsert(UserListing)
            .values(
                user_id=int(data["owner_id"]),
                auction_id=int(data["auction_id"]),
                title=data["title"],
                starting_price=data["starting_price"],
                current_price=data["starting_price"],
                status="active",
                ends_at=datetime.fromisoformat(data["ends_at"]),
            )
            .on_conflict_do_nothing(index_elements=["auction_id"])   # idempotent
        )
        await db.execute(stmt)
        await db.commit()


# ── bid.placed → new highest bidder, previous one flips to outbid ────
async def on_bid_placed(data: dict):
    auction_id = int(data["auction_id"])
    bidder_id  = int(data["bidder_id"])
    amount     = data["amount"]
    title      = data["title"]

    async with AsyncSessionLocal() as db:
        # 1. whoever was highest on this auction is now outbid
        await db.execute(
            update(UserBid)
            .where(UserBid.auction_id == auction_id, UserBid.bid_status == "highest_bidder")
            .values(bid_status="outbid")
        )
        # 2. upsert this bidder as the new highest (one row per user+auction)
        await db.execute(
            upsert(UserBid)
            .values(
                user_id=bidder_id, auction_id=auction_id, title=title,
                your_bid=amount, bid_status="highest_bidder",
            )
            .on_conflict_do_update(
                index_elements=["user_id", "auction_id"],
                set_={"your_bid": amount, "bid_status": "highest_bidder"},
            )
        )
        # 3. reflect the new price on the owner's listing row
        await db.execute(
            update(UserListing)
            .where(UserListing.auction_id == auction_id)
            .values(current_price=amount, highest_bidder=bidder_id)
        )
        await db.commit()


# ── auction.closed → settle everyone: won / lost, listing closed ─────
async def on_auction_closed(data: dict):
    auction_id = int(data["auction_id"])
    winner_id  = data.get("winner_id")
    winner_id  = int(winner_id) if winner_id is not None else None

    async with AsyncSessionLocal() as db:
        await db.execute(
            update(UserListing)
            .where(UserListing.auction_id == auction_id)
            .values(status="closed")
        )
        if winner_id is not None:
            await db.execute(
                update(UserBid)
                .where(UserBid.auction_id == auction_id, UserBid.user_id == winner_id)
                .values(bid_status="won")
            )
            await db.execute(
                update(UserBid)
                .where(UserBid.auction_id == auction_id, UserBid.user_id != winner_id)
                .values(bid_status="lost")
            )
        else:
            # zero-bid auction — no winner, everyone (if any) loses
            await db.execute(
                update(UserBid)
                .where(UserBid.auction_id == auction_id)
                .values(bid_status="lost")
            )
        await db.commit()
        