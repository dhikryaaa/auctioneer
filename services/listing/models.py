from datetime import datetime
from typing import Optional, List
from enum import Enum
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class AuctionStatus(str, Enum):
    active = 'active'
    closing = 'closing'
    closed = 'closed'

class Auction(Base):
    __tablename__ = 'auctions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    starting_price: Mapped[int] = mapped_column(Integer, nullable=False)
    current_price: Mapped[int] = mapped_column(Integer, nullable=False)
    current_bidder_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[AuctionStatus] = mapped_column(String, index=True, nullable=False, default=AuctionStatus.active)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ends_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    