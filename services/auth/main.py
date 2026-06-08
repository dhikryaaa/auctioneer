from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import init_db
from routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="Auth Service", lifespan=lifespan)
app.include_router(router)
