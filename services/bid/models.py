from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from database import Base

class Bid(Base):
    __tablename__ = "bids"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    auction_id = Column(Integer, nullable=False, index=True)
    bidder_id  = Column(Integer, nullable=False, index=True)
    amount     = Column(Integer, nullable=False)
    placed_at  = Column(DateTime, default=datetime.utcnow, nullable=False)
