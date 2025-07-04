"""Permission middleware for Zultra Telegram Bot."""

from telegram import Update
from telegram.ext import ContextTypes
from .base import BaseMiddleware


class PermissionMiddleware(BaseMiddleware):
    """Middleware for permission checking."""
    
    async def process_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Process update for permission checks."""
        if not self.enabled:
            return True
        
        # Permission checking logic would go here
        return True