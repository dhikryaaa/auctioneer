from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class Bid(Base):
    __tablename__ = "bids"

    id:         Mapped[int]      = mapped_column(primary_key=True, autoincrement=True)
    auction_id: Mapped[int]      = mapped_column(index=True)
    bidder_id:  Mapped[int]      = mapped_column(index=True)
    amount:     Mapped[int]      = mapped_column()
    placed_at:  Mapped[datetime] = mapped_column(default=datetime.utcnow)
    