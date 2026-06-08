import httpx
from fastapi import HTTPException
from config import settings

async def get_auction(auction_id: int) -> dict | None:
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            res = await client.get(f"{settings.LISTING_SERVICE_URL}/auctions/{auction_id}")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Listing service unavailable")
        
    if res.status_code == 404:
        return None
    
    res.raise_for_status()
    
    return res.json()

async def accept_bid_on_auction(auction_id: int, new_price: int, expected_version: int) -> bool:
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            res = await client.patch(
                f"{settings.LISTING_SERVICE_URL}/auctions/{auction_id}/price",
                json={"new_price": new_price, "expected_version": expected_version},
            )
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Listing service unavailable")
    
    if res.status_code == 409:
        return False          # someone outbid you between read and write
    
    res.raise_for_status()
    
    return True

async def is_user_banned(user_id: int) -> bool:
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            res = await client.get(f"{settings.AUTH_SERVICE_URL}/users/{user_id}")
        
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Auth service unavailable")
    
    res.raise_for_status()
    
    return res.json().get("is_banned", False)
