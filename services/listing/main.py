from contextlib import asynccontextmanager
from fastapi import FastAPI
import rabbitmq
from database import init_db
from routes import router
from scheduler import scheduler, close_expired_auctions
from consumer import handle_bid_placed
import httpx
import aio_pika


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    app.state.client = httpx.AsyncClient()
    
    connection = await rabbitmq.get_connection()
    channel = await connection.channel()

    rabbitmq.exchange = await channel.declare_exchange(
        name='auctioneer',
        type=aio_pika.ExchangeType.TOPIC,
        durable=True
    )
    
    queue = await channel.declare_queue(
        "listing-service",
        durable=True
    )

    await queue.bind(
        rabbitmq.exchange,
        routing_key="bid.placed"
    )
    
    await queue.consume(handle_bid_placed)
    
    scheduler.add_job(close_expired_auctions, 'interval', seconds=5)
    scheduler.start()
    
    yield

    scheduler.shutdown()
    await app.state.client.aclose()
    await connection.close()

app = FastAPI(title='Listing Service', lifespan=lifespan)
app.include_router(router)

@app.get("/health")
async def health_check():
    return {"status": "Listing service is Running"}

@app.get("/")
async def root():
    return {"message": "Welcome to the Listing Service"}
