from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra fields like host, port (uvicorn params)
    )
    
    # Gemini AI Configuration
    gemini_api_key: str = ""
    gemini_model_name: str = "gemini-2.0-flash"  # Default to gemini-2.0-flash (available and stable)
    
    # Application Configuration
    environment: str = "development"
    debug: bool = False


# Global settings instance
settings = Settings()

