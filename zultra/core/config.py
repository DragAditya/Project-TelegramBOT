"""
Core configuration module for the Zultra Telegram Bot.
Handles environment variables, security settings, and application configuration.
"""

from typing import List, Optional, Union
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings
import os
import sys
from pathlib import Path
from cryptography.fernet import Fernet


class Settings(BaseSettings):
    """Application settings with validation and type safety."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
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
    secret_key: str = Field(default="change-this-secret-key", description="Secret key for sessions")
    
    # AI Providers
    openai_api_key: Optional[str] = Field(None, description="OpenAI API Key")
    gemini_api_key: Optional[str] = Field(None, description="Google Gemini API Key")
    
    # Bot Settings
    environment: str = Field(default="development", description="Environment (development/production)")
    debug: bool = Field(default=True, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    max_workers: int = Field(default=4, description="Maximum worker threads")
    
    # Admin Configuration
    owner_ids: str = Field(default="", description="Comma-separated owner user IDs")
    admin_ids: str = Field(default="", description="Comma-separated admin user IDs")
    
    # Rate Limiting
    rate_limit_messages: int = Field(default=30, description="Message rate limit per window")
    rate_limit_window: int = Field(default=60, description="Rate limit window in seconds")
    ai_rate_limit: int = Field(default=10, description="AI request rate limit per window")
    ai_rate_window: int = Field(default=300, description="AI rate limit window in seconds")
    
    # Webhook Configuration
    webhook_host: str = Field(default="0.0.0.0", description="Webhook host")
    webhook_port: int = Field(default=8000, description="Webhook port")
    webhook_path: str = Field(default="/webhook", description="Webhook path")
    
    @field_validator("owner_ids")
    @classmethod
    def parse_owner_ids(cls, v: str) -> List[int]:
        """Parse owner IDs from comma-separated string."""
        if not v or v.strip() == "":
            return []
        try:
            return [int(x.strip()) for x in v.split(",") if x.strip().isdigit()]
        except (ValueError, AttributeError):
            return []
    
    @field_validator("admin_ids")
    @classmethod
    def parse_admin_ids(cls, v: str) -> List[int]:
        """Parse admin IDs from comma-separated string."""
        if not v or v.strip() == "":
            return []
        try:
            return [int(x.strip()) for x in v.split(",") if x.strip().isdigit()]
        except (ValueError, AttributeError):
            return []
    
    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, v: Optional[str]) -> str:
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
    
    def get_owner_ids(self) -> List[int]:
        """Get parsed owner IDs."""
        return self.parse_owner_ids(self.owner_ids)
    
    def get_admin_ids(self) -> List[int]:
        """Get parsed admin IDs."""
        return self.parse_admin_ids(self.admin_ids)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        try:
            _settings = Settings()
        except Exception as e:
            print(f"Error loading settings: {e}")
            # Create minimal settings for testing
            _settings = Settings(bot_token="test-token")
    return _settings


# Environment-specific configuration
def setup_logging():
    """Setup logging configuration based on environment."""
    from loguru import logger
    import sys
    
    # Remove default handler
    logger.remove()
    
    settings = get_settings()
    
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
        # Ensure logs directory exists
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
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


# Validate configuration on import
def validate_config() -> bool:
    """Validate configuration and return True if valid."""
    try:
        settings = get_settings()
        
        # Check required fields
        if not settings.bot_token or settings.bot_token == "test-token":
            print("⚠️  Warning: BOT_TOKEN not configured")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False