from datetime import datetime
from pydantic import BaseModel, Field

class BidCreate(BaseModel):
    auction_id: int
    amount: int = Field(..., gt=0)
    
class BidResponse(BaseModel):
    id: int
    auction_id: int
    bidder_id: int
    amount: int
    created_at: datetime

    class Config:
        from_attributes = True
        
class AuctionInfo(BaseModel):
    id: int
    owner_id: int
    title: str
    description: str
    starting_price: int
    current_price: int
    current_bidder_id: int | None
    status: str
    version: int
    ends_at: datetime
    created_at: datetime
    