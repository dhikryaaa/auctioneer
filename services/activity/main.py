from contextlib import asynccontextmanager
from fastapi import FastAPI
from observability import instrument_app
from database import init_db
from consumer import start_consumer
from rabbitmq import close_connection
from routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await start_consumer()   # registers the consumer; FastAPI's loop keeps it alive
    yield
    await close_connection()

app = FastAPI(title="Activity Service", lifespan=lifespan)
app.include_router(router)
