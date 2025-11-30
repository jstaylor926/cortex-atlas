"""
Configuration management for Atlas API
"""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Server
    host: str = "127.0.0.1"
    port: int = 4100

    # Database
    database_path: str = "./data/atlas.db"

    # OpenAI
    openai_api_key: Optional[str] = None

    # Google Calendar (optional)
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None

    # AI Models
    chat_model: str = "gpt-4o-mini"
    heavy_model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-large"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


def get_data_dir() -> Path:
    """Get or create data directory"""
    data_dir = Path(settings.database_path).parent
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
