from contextlib import asynccontextmanager
from fastapi import FastAPI

from database import init_db, engine
from rabbitmq import init_rabbitmq, close_rabbitmq
from routes import router
from observability import instrument_app

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_rabbitmq()
    yield
    await close_rabbitmq()

app = FastAPI(title="Bid Service", lifespan=lifespan)
app.include_router(router)
instrument_app(app, service_name="bid-service", engine=engine)
