from datetime import datetime
from pydantic import BaseModel

class ListingOut(BaseModel):
    auction_id: int
    title: str
    current_price: int
    highest_bidder: int | None
    status: str
    ends_at: datetime

    class Config:
        from_attributes = True

class BidOut(BaseModel):
    auction_id: int
    title: str
    your_bid: int
    bid_status: str

    class Config:
        from_attributes = True
        
class ActivityOut(BaseModel):
    listings: list[ListingOut]
    bids: list[BidOut]
    