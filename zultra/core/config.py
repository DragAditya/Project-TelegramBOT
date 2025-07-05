"""
Production-ready configuration module for Zultra Telegram Bot.
Bulletproof settings with comprehensive validation and error handling.
"""

import os
import sys
from typing import List, Optional, Any
from pathlib import Path
from dataclasses import dataclass

from pydantic import BaseSettings, Field, validator, ValidationError
from cryptography.fernet import Fernet
from loguru import logger


class ZultraSettings(BaseSettings):
    """Bulletproof application settings with validation."""
    
    # Bot Configuration
    bot_token: str = Field(..., min_length=45, description="Telegram Bot Token")
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
    secret_key: str = Field(default="change-this-secret-key-in-production", min_length=32)
    
    # AI Providers
    openai_api_key: Optional[str] = Field(None, description="OpenAI API Key")
    gemini_api_key: Optional[str] = Field(None, description="Google Gemini API Key")
    
    # Environment Settings
    environment: str = Field(default="development", regex="^(development|production|testing)$")
    debug: bool = Field(default=True, description="Debug mode")
    log_level: str = Field(default="INFO", regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    
    # Admin Configuration
    owner_ids: str = Field(default="", description="Comma-separated owner user IDs")
    admin_ids: str = Field(default="", description="Comma-separated admin user IDs")
    
    # Rate Limiting
    rate_limit_messages: int = Field(default=30, ge=1, le=1000)
    rate_limit_window: int = Field(default=60, ge=1, le=3600)
    ai_rate_limit: int = Field(default=10, ge=1, le=100)
    ai_rate_window: int = Field(default=300, ge=60, le=3600)
    
    # Performance Settings
    max_workers: int = Field(default=4, ge=1, le=32)
    connection_pool_size: int = Field(default=10, ge=1, le=100)
    
    # Webhook Configuration
    webhook_host: str = Field(default="0.0.0.0")
    webhook_port: int = Field(default=8000, ge=1000, le=65535)
    webhook_path: str = Field(default="/webhook")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        validate_assignment = True
        
    @validator("bot_token")
    def validate_bot_token(cls, v):
        """Validate Telegram bot token format."""
        if not v or v == "your_telegram_bot_token_here":
            raise ValueError("BOT_TOKEN must be set to a valid Telegram bot token")
        
        # Basic Telegram bot token format validation
        if not v.count(':') == 1:
            raise ValueError("Invalid bot token format")
        
        bot_id, token = v.split(':')
        if not bot_id.isdigit() or len(token) != 35:
            raise ValueError("Invalid bot token format")
        
        return v
    
    @validator("database_url")
    def validate_database_url(cls, v, values):
        """Validate database URL."""
        if not v:
            raise ValueError("DATABASE_URL cannot be empty")
        
        # Check for production requirements
        environment = values.get('environment', 'development')
        if environment == 'production' and 'sqlite' in v.lower():
            logger.warning("SQLite not recommended for production. Consider PostgreSQL.")
        
        return v
    
    @validator("encryption_key")
    def validate_encryption_key(cls, v):
        """Generate or validate encryption key."""
        if not v:
            # Generate a new key
            key = Fernet.generate_key()
            logger.info("Generated new encryption key")
            return key.decode()
        
        try:
            # Validate existing key
            Fernet(v.encode())
            return v
        except Exception:
            # Generate new key if invalid
            key = Fernet.generate_key()
            logger.warning("Invalid encryption key provided, generated new one")
            return key.decode()
    
    @validator("owner_ids")
    def validate_owner_ids(cls, v):
        """Validate owner IDs format."""
        if not v or v.strip() == "":
            logger.warning("No owner IDs configured - bot will have limited functionality")
            return []
        
        try:
            ids = [int(x.strip()) for x in v.split(",") if x.strip().isdigit()]
            if not ids:
                logger.warning("No valid owner IDs found")
            return ids
        except Exception:
            logger.error("Invalid owner IDs format")
            return []
    
    @validator("admin_ids")
    def validate_admin_ids(cls, v):
        """Validate admin IDs format."""
        if not v or v.strip() == "":
            return []
        
        try:
            return [int(x.strip()) for x in v.split(",") if x.strip().isdigit()]
        except Exception:
            logger.error("Invalid admin IDs format")
            return []
    
    @validator("webhook_url")
    def validate_webhook_url(cls, v, values):
        """Validate webhook URL."""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError("Webhook URL must start with http:// or https://")
        return v
    
    def get_owner_ids(self) -> List[int]:
        """Get validated owner IDs."""
        if isinstance(self.owner_ids, list):
            return self.owner_ids
        return self.validate_owner_ids(self.owner_ids)
    
    def get_admin_ids(self) -> List[int]:
        """Get validated admin IDs."""
        if isinstance(self.admin_ids, list):
            return self.admin_ids
        return self.validate_admin_ids(self.admin_ids)
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"
    
    @property
    def is_debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self.debug and not self.is_production
    
    @property
    def fernet_cipher(self) -> Fernet:
        """Get Fernet cipher for encryption/decryption."""
        key = self.encryption_key.encode() if isinstance(self.encryption_key, str) else self.encryption_key
        return Fernet(key)
    
    def encrypt_data(self, data: str) -> bytes:
        """Encrypt sensitive data."""
        return self.fernet_cipher.encrypt(data.encode())
    
    def decrypt_data(self, encrypted_data: bytes) -> str:
        """Decrypt sensitive data."""
        return self.fernet_cipher.decrypt(encrypted_data).decode()


@dataclass
class RuntimeConfig:
    """Runtime configuration and state."""
    start_time: float
    version: str = "2.0.0"
    startup_errors: List[str] = None
    health_status: dict = None
    
    def __post_init__(self):
        if self.startup_errors is None:
            self.startup_errors = []
        if self.health_status is None:
            self.health_status = {}


class ConfigManager:
    """Centralized configuration manager with error handling."""
    
    def __init__(self):
        self.settings: Optional[ZultraSettings] = None
        self.runtime: Optional[RuntimeConfig] = None
        self.is_initialized = False
        self.initialization_errors = []
    
    def initialize(self) -> bool:
        """Initialize configuration with comprehensive error handling."""
        try:
            # Load settings
            self.settings = ZultraSettings()
            
            # Initialize runtime config
            import time
            self.runtime = RuntimeConfig(start_time=time.time())
            
            # Validate critical settings
            self._validate_critical_settings()
            
            # Setup logging
            self._setup_logging()
            
            self.is_initialized = True
            logger.success("Configuration initialized successfully")
            return True
            
        except ValidationError as e:
            error_msg = f"Configuration validation failed: {e}"
            self.initialization_errors.append(error_msg)
            logger.error(error_msg)
            return False
            
        except Exception as e:
            error_msg = f"Unexpected configuration error: {e}"
            self.initialization_errors.append(error_msg)
            logger.error(error_msg)
            return False
    
    def _validate_critical_settings(self) -> None:
        """Validate critical settings for production readiness."""
        if not self.settings:
            raise ValueError("Settings not loaded")
        
        critical_checks = []
        
        # Bot token check
        if not self.settings.bot_token or self.settings.bot_token == "your_telegram_bot_token_here":
            critical_checks.append("BOT_TOKEN not configured")
        
        # Production checks
        if self.settings.is_production:
            if "sqlite" in self.settings.database_url.lower():
                critical_checks.append("SQLite not recommended for production")
            
            if self.settings.secret_key == "change-this-secret-key-in-production":
                critical_checks.append("Default secret key in production")
            
            if not self.settings.get_owner_ids():
                critical_checks.append("No owner IDs configured for production")
        
        if critical_checks:
            logger.warning(f"Critical configuration issues: {critical_checks}")
            self.runtime.startup_errors.extend(critical_checks)
    
    def _setup_logging(self) -> None:
        """Setup production-ready logging."""
        try:
            logger.remove()  # Remove default handler
            
            # Console handler
            log_format = (
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            )
            
            logger.add(
                sys.stdout,
                format=log_format,
                level=self.settings.log_level,
                colorize=True,
                backtrace=self.settings.is_debug,
                diagnose=self.settings.is_debug,
                catch=True
            )
            
            # File handler for production
            if self.settings.is_production:
                logs_dir = Path("logs")
                logs_dir.mkdir(exist_ok=True)
                
                logger.add(
                    logs_dir / "zultra_bot.log",
                    format=log_format,
                    level="INFO",
                    rotation="10 MB",
                    retention="30 days",
                    compression="gzip",
                    backtrace=False,
                    diagnose=False,
                    catch=True
                )
                
                # Error log
                logger.add(
                    logs_dir / "errors.log",
                    format=log_format,
                    level="ERROR",
                    rotation="10 MB",
                    retention="90 days",
                    compression="gzip",
                    catch=True
                )
                
        except Exception as e:
            print(f"Failed to setup logging: {e}")
    
    def get_health_status(self) -> dict:
        """Get comprehensive health status."""
        if not self.is_initialized:
            return {"status": "not_initialized", "errors": self.initialization_errors}
        
        import time
        uptime = time.time() - self.runtime.start_time
        
        health = {
            "status": "healthy" if not self.runtime.startup_errors else "degraded",
            "uptime_seconds": uptime,
            "version": self.runtime.version,
            "environment": self.settings.environment,
            "startup_errors": self.runtime.startup_errors,
            "configuration": {
                "database": "configured" if self.settings.database_url else "missing",
                "redis": "configured" if self.settings.redis_url else "not_configured",
                "ai_providers": {
                    "openai": "configured" if self.settings.openai_api_key else "not_configured",
                    "gemini": "configured" if self.settings.gemini_api_key else "not_configured"
                },
                "owners": len(self.settings.get_owner_ids()),
                "admins": len(self.settings.get_admin_ids())
            }
        }
        
        return health
    
    def reload_settings(self) -> bool:
        """Reload settings from environment/file."""
        try:
            old_settings = self.settings
            self.settings = ZultraSettings()
            
            # Re-validate
            self._validate_critical_settings()
            
            logger.info("Settings reloaded successfully")
            return True
            
        except Exception as e:
            # Restore old settings on failure
            self.settings = old_settings
            logger.error(f"Failed to reload settings: {e}")
            return False


# Global configuration manager
config_manager = ConfigManager()


def get_settings() -> ZultraSettings:
    """Get application settings."""
    if not config_manager.is_initialized:
        success = config_manager.initialize()
        if not success:
            logger.critical("Configuration initialization failed")
            sys.exit(1)
    
    return config_manager.settings


def get_runtime_config() -> RuntimeConfig:
    """Get runtime configuration."""
    if not config_manager.is_initialized:
        config_manager.initialize()
    
    return config_manager.runtime


def initialize_config() -> bool:
    """Initialize configuration system."""
    return config_manager.initialize()


def get_health_status() -> dict:
    """Get system health status."""
    return config_manager.get_health_status()


# Auto-initialize on import in production
if os.getenv("ENVIRONMENT", "development").lower() == "production":
    initialize_config()