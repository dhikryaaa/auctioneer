from datetime import datetime
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class UserListing(Base):
    __tablename__ = "user_listings"
    __table_args__ = (UniqueConstraint("auction_id", name="uq_listing_auction"),)

    id:             Mapped[int]            = mapped_column(primary_key=True, autoincrement=True)
    user_id:        Mapped[int]            = mapped_column(index=True)   # the owner
    auction_id:     Mapped[int]            = mapped_column(index=True)
    title:          Mapped[str]
    starting_price: Mapped[int]            = mapped_column()
    current_price:  Mapped[int]            = mapped_column()
    highest_bidder: Mapped[int | None]     = mapped_column()
    status:         Mapped[str]            = mapped_column(default="active")  # active | closed
    ends_at:        Mapped[datetime]
    created_at:     Mapped[datetime]       = mapped_column(default=datetime.utcnow)

class UserBid(Base):
    __tablename__ = "user_bids"
    __table_args__ = (UniqueConstraint("user_id", "auction_id", name="uq_bid_user_auction"),)

    id:           Mapped[int]      = mapped_column(primary_key=True, autoincrement=True)
    user_id:      Mapped[int]      = mapped_column(index=True)
    auction_id:   Mapped[int]      = mapped_column(index=True)
    title:        Mapped[str]
    your_bid:     Mapped[int]      = mapped_column()
    bid_status:   Mapped[str]      # highest_bidder | outbid | won | lost
    placed_at:    Mapped[datetime] = mapped_column(default=datetime.utcnow)
    