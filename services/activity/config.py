from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../../.env", extra="ignore")

    DATABASE_URL: str = "sqlite+aiosqlite:///data/database.db"
    RABBITMQ_URL: str
    EXCHANGE_NAME: str = "auctioneer"
    QUEUE_NAME: str = "activity_queue"

settings = Settings() # type: ignore