from datetime import datetime
from typing import Optional
from enum import Enum
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import field_validator
from datetime import timezone
from database import Base

class AuctionStatus(str, Enum):
    active = 'active'
    closed = 'closed'

class Auction(Base):
    __tablename__ = 'auctions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    starting_price: Mapped[int] = mapped_column(Integer, nullable=False)
    current_price: Mapped[int] = mapped_column(Integer, nullable=False)
    current_bidder_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[AuctionStatus] = mapped_column(String, index=True, nullable=False, default=AuctionStatus.active)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ends_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    @field_validator('ends_at', 'created_at')
    @classmethod
    def force_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is not None:
            return v.astimezone(timezone.utc).replace(tzinfo=None)  # convert to UTC naive
        return v  # assume already UTC naive