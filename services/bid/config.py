from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    DATABASE_URL: str = "sqlite+aiosqlite:///data/database.db"
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 15
    REFRESH_TOKEN_DAYS: int = 7
    COOKIES_SECURE: bool = False
    LISTING_SERVICE_URL: str
    AUTH_SERVICE_URL: str
        
settings = Settings() # type: ignore