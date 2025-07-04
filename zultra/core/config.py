"""
Core configuration module for the Zultra Telegram Bot.
Handles environment variables, security settings, and application configuration.
"""

from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings
import base64
import os
from cryptography.fernet import Fernet


class Settings(BaseSettings):
    """Application settings with validation and type safety."""
    
    # Bot Configuration
    bot_token: str = Field(..., description="Telegram Bot Token")
    bot_username: Optional[str] = Field(None, description="Bot Username")
    bot_webhook_url: Optional[str] = Field(None, description="Webhook URL for production")
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite+aiosqlite:///./zultra_bot.db",
        description="Database connection URL"
    )
    
    # Redis Configuration
    redis_url: Optional[str] = Field(None, description="Redis connection URL")
    
    # Security
    encryption_key: Optional[str] = Field(None, description="Encryption key for sensitive data")
    secret_key: str = Field(default="your-secret-key-change-this", description="Secret key for sessions")
    
    # AI Providers
    openai_api_key: Optional[str] = Field(None, description="OpenAI API Key")
    gemini_api_key: Optional[str] = Field(None, description="Google Gemini API Key")
    
    # Bot Settings
    environment: str = Field(default="development", description="Environment (development/production)")
    debug: bool = Field(default=True, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    max_workers: int = Field(default=4, description="Maximum worker threads")
    
    # Admin Configuration
    owner_ids: List[int] = Field(default_factory=list, description="Bot owner user IDs")
    admin_ids: List[int] = Field(default_factory=list, description="Bot admin user IDs")
    
    # Rate Limiting
    rate_limit_messages: int = Field(default=30, description="Message rate limit per window")
    rate_limit_window: int = Field(default=60, description="Rate limit window in seconds")
    ai_rate_limit: int = Field(default=10, description="AI request rate limit per window")
    ai_rate_window: int = Field(default=300, description="AI rate limit window in seconds")
    
    # Webhook Configuration
    webhook_host: str = Field(default="0.0.0.0", description="Webhook host")
    webhook_port: int = Field(default=8000, description="Webhook port")
    webhook_path: str = Field(default="/webhook", description="Webhook path")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator("owner_ids", pre=True)
    def parse_owner_ids(cls, v):
        """Parse owner IDs from comma-separated string."""
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip().isdigit()]
        return v if v else []
    
    @validator("admin_ids", pre=True)
    def parse_admin_ids(cls, v):
        """Parse admin IDs from comma-separated string."""
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip().isdigit()]
        return v if v else []
    
    @validator("encryption_key", pre=True)
    def validate_encryption_key(cls, v):
        """Generate or validate encryption key."""
        if not v:
            # Generate a new key if none provided
            return Fernet.generate_key().decode()
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def is_debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self.debug and not self.is_production
    
    @property
    def fernet_key(self) -> Fernet:
        """Get Fernet encryption instance."""
        key = self.encryption_key.encode() if isinstance(self.encryption_key, str) else self.encryption_key
        return Fernet(key)
    
    def get_database_url(self) -> str:
        """Get the appropriate database URL for the environment."""
        if self.is_production and "sqlite" in self.database_url:
            # Force PostgreSQL in production
            raise ValueError("SQLite is not recommended for production. Use PostgreSQL.")
        return self.database_url


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


# Environment-specific configuration
def setup_logging():
    """Setup logging configuration based on environment."""
    from loguru import logger
    import sys
    
    # Remove default handler
    logger.remove()
    
    # Console handler with appropriate level
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=settings.is_debug
    )
    
    # File handler for production
    if settings.is_production:
        logger.add(
            "logs/zultra_bot.log",
            format=log_format,
            level="INFO",
            rotation="1 day",
            retention="30 days",
            compression="gzip",
            backtrace=True,
            diagnose=False
        )
    
    return logger