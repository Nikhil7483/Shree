"""
Application configuration using pydantic-settings.
Loads environment variables from .env file.
"""

from functools import lru_cache
from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # MongoDB (Supports local, Atlas MONGODB_URL, and Railway MONGO_URL / MONGO_PRIVATE_URL)
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGO_URL: Optional[str] = None
    MONGO_PRIVATE_URL: Optional[str] = None
    DB_NAME: str = "shree_temple"

    @model_validator(mode="after")
    def resolve_mongo_url(self) -> "Settings":
        """Automatically resolve Railway or Cloud MongoDB variables."""
        if self.MONGO_PRIVATE_URL:
            self.MONGODB_URL = self.MONGO_PRIVATE_URL
        elif self.MONGO_URL:
            self.MONGODB_URL = self.MONGO_URL
        return self

    # JWT
    JWT_SECRET_KEY: str = "shree-shanishwara-temple-jwt-secret-2024-dev"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Razorpay
    RAZORPAY_KEY_ID: str = "rzp_test_placeholder"
    RAZORPAY_KEY_SECRET: str = "placeholder_secret"

    # Admin
    ADMIN_EMAIL: str = "admin@shreeshani.com"
    ADMIN_PASSWORD: str = "Admin@123"

    # App
    APP_NAME: str = "Shree Shanishwara Swamy Temple"
    APP_ENV: str = "development"
    ALLOWED_ORIGINS: str = "*"
    ENABLE_DOCS: bool = False

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance to avoid reading .env on every call."""
    return Settings()
