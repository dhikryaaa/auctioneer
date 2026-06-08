from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Bid
from schemas import BidCreate, BidResponse
from dependencies import get_current_user, require_admin
import clients
from publisher import publish_bid_placed

router = APIRouter()


# ── POST /bids — place a bid (user) ──────────────────────────────
@router.post("/", response_model=BidResponse, status_code=201)
async def place_bid(
    bid: BidCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    auction_id = bid.auction_id

    # 1. auction must exist (HTTP -> listing)
    auction = await clients.get_auction(auction_id)
    if auction is None:
        raise HTTPException(status_code=404, detail="Auction not found")

    # 2. banned users can't bid (HTTP -> auth) — your RBAC feature
    if await clients.is_user_banned(user["user_id"]):
        raise HTTPException(status_code=403, detail="You are banned from bidding")

    # 3. can't bid on your own auction
    if auction["owner_id"] == user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot bid on your own auction")

    # 4. auction must still be open
    if auction["status"] != "active" or datetime.fromisoformat(auction["ends_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Auction has ended")

    # 5. bid must beat current price
    if bid.amount <= int(auction["current_price"]):
        raise HTTPException(status_code=400, detail="Bid too low")

    # 6. atomic accept on listing (optimistic lock). False = outrun by a concurrent bid
    accepted = await clients.accept_bid_on_auction(
        auction_id, bid.amount, auction["version"]
    )
    if not accepted:
        raise HTTPException(status_code=409, detail="Bid was outrun, please retry")

    # 7. record the bid in our own ledger
    new_bid = Bid(auction_id=bid.auction_id, bidder_id=user["user_id"], amount=bid.amount)
    db.add(new_bid)
    await db.commit()
    await db.refresh(new_bid)

    # 8. fire the event (after the bid is committed)
    await publish_bid_placed(
        auction_id=auction_id,
        title=auction["title"],
        bidder_id=user["user_id"],
        version=auction["version"] + 1,
        amount=bid.amount,
        previous_bidder_id=auction.get("current_bidder_id"),
        placed_at=new_bid.placed_at,
    )

    return new_bid


# ── GET /bids/me — my raw bid records (user) ─────────────────────
@router.get("/me", response_model=list[BidResponse])
async def my_bids(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Bid).where(Bid.bidder_id == user["user_id"]))
    return result.scalars().all()


# ── GET /bids/{auction_id} — public bid history for an auction ───
@router.get("/{auction_id}", response_model=list[BidResponse])
async def auction_bids(auction_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Bid).where(Bid.auction_id == auction_id).order_by(Bid.placed_at.desc())
    )
    return result.scalars().all()


# ── GET /bids — admin: every bid in the system ───────────────────
@router.get("/", response_model=list[BidResponse])
async def all_bids(admin: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Bid).order_by(Bid.placed_at.desc()))
    return result.scalars().all()