import aio_pika
import json
from models import Auction
import rabbitmq

async def publish_auction_created(auction: Auction):
    assert rabbitmq.exchange is not None
    await rabbitmq.exchange.publish(
        aio_pika.Message(
            body=json.dumps({
                "auction_id": auction.id,
                "owner_id": auction.owner_id,
                "title": auction.title,
                "description": auction.description,
                "starting_price": auction.starting_price,
                "ends_at": auction.ends_at.isoformat(),
                "created_at": auction.created_at.isoformat()
            }).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        ),
        routing_key="auction.created"
    )

async def publish_auction_closed(auction: Auction):
    assert rabbitmq.exchange is not None
    await rabbitmq.exchange.publish(
        aio_pika.Message(
            body=json.dumps({
                "auction_id": auction.id,
                "owner_id": auction.owner_id,
                "winner_id": auction.current_bidder_id,
                "title": auction.title,
                "description": auction.description,
                "final_price": auction.current_price,
                "closed_at": auction.ends_at.isoformat()
            }).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        ),
        routing_key='auction.closed'
    )
    
async def publish_auction_deleted(auction):
    assert rabbitmq.exchange is not None
    await rabbitmq.exchange.publish(
        aio_pika.Message(
            body=json.dumps({
                "auction_id": auction.id,
                "owner_id": auction.owner_id,
            }).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        ),
        routing_key="auction.deleted"
    )