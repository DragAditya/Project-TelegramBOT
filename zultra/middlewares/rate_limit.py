"""
Rate limiting middleware for Zultra Telegram Bot.
Prevents spam and abuse by limiting message rates.
"""

import time
from collections import defaultdict
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from .base import BaseMiddleware
from ..core.config import get_settings


class RateLimitMiddleware(BaseMiddleware):
    """Middleware for rate limiting users."""
    
    def __init__(self):
        super().__init__("RateLimitMiddleware")
        self.user_requests = defaultdict(list)
        self.settings = get_settings()
    
    async def _process_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check rate limits."""
        if not update.effective_user:
            return True
        
        user_id = update.effective_user.id
        current_time = time.time()
        
        # Clean old requests
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if current_time - req_time < self.settings.rate_limit_window
        ]
        
        # Check if user exceeded rate limit
        if len(self.user_requests[user_id]) >= self.settings.rate_limit_messages:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            if update.message:
                await update.message.reply_text(
                    f"⚠️ Slow down! You're sending messages too quickly. "
                    f"Please wait {self.settings.rate_limit_window} seconds."
                )
            return False
        
        # Add current request
        self.user_requests[user_id].append(current_time)
        return True