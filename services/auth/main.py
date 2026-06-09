from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import init_db, engine
from routes import router
from observability import instrument_app

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="Auth Service", lifespan=lifespan)
app.include_router(router)
instrument_app(app, service_name="auth-service", engine=engine)
