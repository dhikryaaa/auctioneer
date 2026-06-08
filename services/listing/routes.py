import os
from fastapi import APIRouter, HTTPException
from httpx import delete
from sqlalchemy import select
from dependencies import CurrentUser, AdminUser, DB, HttpClient
from schemas import AuctionCreateRequest, AuctionOut, AuctionUpdateRequest
from models import Auction, AuctionStatus
from publisher import publish_auction_created, publish_auction_closed, publish_auction_deleted
router = APIRouter()

BID_SERVICE_URL = os.getenv('BID_SERVICE_URL','')


@router.get('/', response_model=list[AuctionOut])
async def get_all_active_auctions(db: DB):
    result = await db.execute(select(Auction).where(Auction.status == AuctionStatus.active))
    auctions = result.scalars().all()
    
    return auctions

@router.get('/all', response_model=list[AuctionOut])
async def get_all_auctions(user: AdminUser, db: DB):
    result = await db.execute(select(Auction))
    auctions = result.scalars().all()
    
    return auctions

@router.get('/{id}', response_model=AuctionOut)
async def get_auction_by_id(id: int, db: DB):
    auction = await db.get(Auction, id)
    
    if auction is None:
        raise HTTPException(404, detail=f'Cannot find auction by id: {id}')
    
    return auction


@router.post('/', response_model=AuctionOut)
async def create_auction(request: AuctionCreateRequest, user: CurrentUser, db: DB):
    
    auction = Auction(
        owner_id= user['user_id'],
        title=request.title,
        description=request.description,
        starting_price=request.starting_price,
        current_price=request.starting_price,
        current_bidder_id=None,
        ends_at=request.ends_at
    )
    
    db.add(auction)
    
    await db.commit()
    await db.refresh(auction)
    
    # Send event auction.created
    await publish_auction_created(auction=auction)
    
    return auction


@router.patch('/{id}', response_model=AuctionOut)
async def edit_auction_by_id(id: int, request: AuctionUpdateRequest, user: CurrentUser, db: DB, client: HttpClient):
    auction = await db.get(Auction, id)
    
    if auction is None:
        raise HTTPException(status_code=404, detail=f'No auction with id: {id}')
    
    if auction.owner_id != user['user_id']:
        raise HTTPException(status_code=403, detail='Forbidden')
    
    # Hit bidding service to check if auction already has bids, if yes then return
    res = await client.get(f"{BID_SERVICE_URL}/bids/{id}")
    
    if res.status_code == 200 and len(res.json()) > 0:
        raise HTTPException(status_code=400, detail='Cannot edit an auction that already has bids')

    updated_data = request.model_dump(exclude_unset=True)
    for field, value in updated_data.items():
        setattr(auction, field, value)
        
    await db.commit()
    await db.refresh(auction)
    
    return auction
    
    
@router.delete('/{id}', status_code=200)
async def delete_auction_by_id(id: int, user: CurrentUser, db: DB, client: HttpClient):
    auction = await db.get(Auction, id)
    
    if auction is None:
        raise HTTPException(status_code=404, detail=f'No auction with id: {id}')
    
    if auction.owner_id != user['user_id']:
        raise HTTPException(status_code=403, detail='Forbidden')
    
    # Hit bidding service to check if auction already has bids, if yes then return
    res = await client.get(f"{BID_SERVICE_URL}/bids/{id}")
    
    if res.status_code == 200 and len(res.json()) > 0:
        raise HTTPException(status_code=400, detail='Cannot edit an auction that already has bids')
    
    await db.delete(auction)
    await db.commit()
    
    return { 'message': 'Sucessfully deleted auction', 'auction': auction }


@router.patch('/{id}/close')
async def force_close_auction_by_id(
    id: int,
    user: AdminUser, 
    db: DB
    ):
    auction = await db.get(Auction, id)
    
    if auction is None:
        raise HTTPException(status_code=404, detail=f'No auction with id: {id}')
    
    if auction.status is AuctionStatus.closed:
        raise HTTPException(status_code=400, detail=f'Auction at  id: {id} is already closed')
    
    setattr(auction, 'status', AuctionStatus.closed)
    
    await db.commit()
    await db.refresh(auction)
    
    # Send auction.close event to activity via msg broker
    await publish_auction_closed(auction)
    
    return auction

@router.delete('/{id}/admin', status_code=200)
async def force_delete_listing_admin(
    id: int, 
    user: AdminUser,
    db:  DB
    ):
    auction = await db.get(Auction, id)
    
    if auction is None:
        raise HTTPException(status_code=404, detail=f'No auction with id: {id}')
    
    await db.delete(auction)
    await db.commit()
    
    # Send auction.delete event to bidding to remove bids on said auction
    await publish_auction_deleted(auction)
    
    return { 'message': 'Sucessfully deleted auction', 'auction': auction}

