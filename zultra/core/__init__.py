"""
Core package for Zultra Telegram Bot.
Contains configuration, bot initialization, and error handling.
"""

from .config import settings, get_settings, setup_logging
from .bot import ZultraBot
from .errors import *

__all__ = [
    "settings",
    "get_settings", 
    "setup_logging",
    "ZultraBot",
    "BotError",
    "ValidationError",
    "RateLimitError",
    "PermissionError",
    "DatabaseError"
]