from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_url: str = "postgresql://user:pass@localhost:5432/inventory"
    kafka_broker: str = "localhost:9092"
    anthropic_api_key: str = "your_key_here"
    pinecone_api_key: str = "your_key_here"
    sendgrid_api_key: str = "your_key_here"
    slack_webhook_url: str = "your_key_here"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()