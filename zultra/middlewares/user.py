"""User middleware for Zultra Telegram Bot."""

from telegram import Update
from telegram.ext import ContextTypes
from .base import BaseMiddleware


class UserMiddleware(BaseMiddleware):
    """Middleware for user tracking."""
    
    async def process_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Process update for user tracking."""
        if not self.enabled:
            return True
        
        # User tracking logic would go here
        return True