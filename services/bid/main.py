from contextlib import asynccontextmanager
from fastapi import FastAPI

from database import init_db
from rabbitmq import init_rabbitmq, close_rabbitmq
from routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_rabbitmq()
    yield
    await close_rabbitmq()

app = FastAPI(title="Bid Service", lifespan=lifespan)
app.include_router(router)

app.get("/health")
async def health_check():
    return {"status": "Bid service is Running"}

app.get("/")
async def root():
    return {"message": "Welcome to the Bid Service"}
