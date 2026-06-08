from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///data/database.db"
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY', '')
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 15
    REFRESH_TOKEN_DAYS: int = 7
    COOKIES_SECURE: bool = False
    
    class Config:
        env_file = ".env"
        
settings = Settings()
