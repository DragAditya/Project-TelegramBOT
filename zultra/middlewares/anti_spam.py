"""Anti-spam middleware for Zultra Telegram Bot."""

from telegram import Update
from telegram.ext import ContextTypes
from .base import BaseMiddleware


class AntiSpamMiddleware(BaseMiddleware):
    """Middleware for anti-spam protection."""
    
    async def process_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Process update for spam detection."""
        if not self.enabled:
            return True
        
        # Anti-spam logic would go here
        return True