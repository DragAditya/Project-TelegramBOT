"""
Anti-spam middleware for Zultra Telegram Bot.
Detects and prevents spam messages.
"""

import time
from collections import defaultdict
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from .base import BaseMiddleware


class AntiSpamMiddleware(BaseMiddleware):
    """Middleware for spam detection and prevention."""
    
    def __init__(self):
        super().__init__("AntiSpamMiddleware")
        self.user_messages = defaultdict(list)
        self.spam_keywords = ['spam', 'scam', 'bitcoin', 'crypto', 'investment']
    
    async def _process_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check for spam patterns."""
        if not update.message or not update.message.text:
            return True
        
        user_id = update.effective_user.id
        message_text = update.message.text.lower()
        
        # Check for spam keywords
        if any(keyword in message_text for keyword in self.spam_keywords):
            logger.warning(f"Spam keyword detected from user {user_id}")
            await update.message.reply_text("⚠️ Message contains suspicious content.")
            return False
        
        # Check for repeated messages
        current_time = time.time()
        self.user_messages[user_id].append((current_time, message_text))
        
        # Keep only recent messages
        self.user_messages[user_id] = [
            (msg_time, msg_text) for msg_time, msg_text in self.user_messages[user_id]
            if current_time - msg_time < 60  # Last 60 seconds
        ]
        
        # Check for spam patterns
        recent_messages = [msg_text for _, msg_text in self.user_messages[user_id]]
        if len(recent_messages) >= 3 and len(set(recent_messages)) == 1:
            logger.warning(f"Spam pattern detected from user {user_id}")
            await update.message.reply_text("⚠️ Please don't repeat the same message.")
            return False
        
        return True