from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from models import AuctionStatus

class AuctionOut(BaseModel):
    id: int
    owner_id: int
    title: str
    description: Optional[str]
    starting_price: int
    current_price: int
    status: AuctionStatus
    ends_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True
    
class AuctionCreateRequest(BaseModel):
    title: str
    description: Optional[str]
    starting_price: int
    ends_at: datetime
    
class AuctionUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    starting_price: Optional[int] = None
    ends_at: Optional[datetime] = None

    