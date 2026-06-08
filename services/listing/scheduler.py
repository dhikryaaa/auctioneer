# scheduler.py
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from datetime import datetime, timezone
from database import AsyncSession, engine
from models import Auction, AuctionStatus
from publisher import publish_auction_closed

scheduler = AsyncIOScheduler()

async def close_expired_auctions():
    print(datetime.now())
    async with AsyncSession(engine) as db:
        result = await db.execute(
            select(Auction).where(
                Auction.status == AuctionStatus.active,
                Auction.ends_at <= datetime.now(timezone.utc).replace(tzinfo=None)
            )
        )
        auctions = result.scalars().all()

        for auction in auctions:
            auction.status = AuctionStatus.closed

        await db.commit()  # commit first

        for auction in auctions:
            await db.refresh(auction)
            await publish_auction_closed(auction=auction)  # then publish