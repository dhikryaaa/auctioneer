from datetime import datetime
from sqlalchemy import Column, Integer, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from .database import Base

class Bid(Base):
    __tablename__ = "bids"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    auction_id = Column(Integer, nullable=False, index=True)
    bidder_id  = Column(Integer, nullable=False, index=True)
    amount     = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)