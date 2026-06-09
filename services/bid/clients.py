import httpx
from fastapi import HTTPException
from config import settings

async def get_auction(auction_id: int) -> dict | None:
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            res = await client.get(f"{settings.LISTING_SERVICE_URL}/{auction_id}")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Listing service unavailable")
        
    if res.status_code == 404:
        return None
    
    res.raise_for_status()
    
    return res.json()

