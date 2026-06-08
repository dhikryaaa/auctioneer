import json
import aio_pika
from rabbitmq import get_exchange
from datetime import datetime

async def publish_bid_placed(auction_id: int, title: str, bidder_id: int, amount: int, previous_bidder_id: int, placed_at: datetime):
    exchange = get_exchange()
    await exchange.publish(
        aio_pika.Message(
            body=json.dumps({
                "auction_id": auction_id,
                "title": title,
                "bidder_id": bidder_id,
                "amount": amount,
                "previous_bidder_id": previous_bidder_id,
                "placed_at": placed_at.isoformat(),
            }).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),
        routing_key="bid.placed",
    )
    