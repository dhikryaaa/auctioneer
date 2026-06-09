from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user, require_admin
from models import UserListing, UserBid
from schemas import ActivityOut, ListingOut, BidOut

router = APIRouter()


@router.get("/me", response_model=ActivityOut)
async def my_activity(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    uid = user["user_id"]

    query_listings = select(UserListing).where(UserListing.user_id == uid)
    query_bids = select(UserBid).where(UserBid.user_id == uid)

    listings = (await db.execute(query_listings)).scalars().all()
    bids = (await db.execute(query_bids)).scalars().all()

    return {"listings": listings, "bids": bids}


@router.get("/me/listings", response_model=list[ListingOut])
async def my_listings(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(UserListing).where(UserListing.user_id == user["user_id"])
    rows = (await db.execute(query)).scalars().all()
    return rows


@router.get("/me/bids", response_model=list[BidOut])
async def my_bids(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(UserBid).where(UserBid.user_id == user["user_id"])
    rows = (await db.execute(query)).scalars().all()
    return rows

@router.get("/{user_id}", response_model=ActivityOut)
async def user_activity(
    user_id: int,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query_listings = select(UserListing).where(UserListing.user_id == user_id)
    query_bids = select(UserBid).where(UserBid.user_id == user_id)

    listings = (await db.execute(query_listings)).scalars().all()
    bids = (await db.execute(query_bids)).scalars().all()

    return {"listings": listings, "bids": bids}
