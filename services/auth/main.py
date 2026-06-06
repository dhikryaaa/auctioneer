from fastapi import FastAPI
from routes import router

app = FastAPI(title="Auth Service")
app.include_router(router)

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "Auth service is Running"}

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to the Auth Service"}