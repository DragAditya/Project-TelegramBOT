"""
User tracking middleware for Zultra Telegram Bot.
Tracks user interactions and maintains user database.
"""

from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from .base import BaseMiddleware
from ..db.database import create_or_update_user, create_or_update_group


class UserMiddleware(BaseMiddleware):
    """Middleware for tracking users and groups."""
    
    def __init__(self):
        super().__init__("UserMiddleware")
    
    async def _process_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Track user and group data."""
        try:
            # Track user
            if update.effective_user:
                await self._track_user(update.effective_user)
            
            # Track group/chat
            if update.effective_chat and update.effective_chat.type != 'private':
                await self._track_group(update.effective_chat)
        
        except Exception as e:
            logger.error(f"Error in user middleware: {e}")
        
        return True
    
    async def _track_user(self, user):
        """Track user information."""
        user_data = {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_bot': user.is_bot,
            'language_code': user.language_code,
            'is_premium': getattr(user, 'is_premium', False),
            'last_seen': __import__('datetime').datetime.now()
        }
        
        await create_or_update_user(user_data)
    
    async def _track_group(self, chat):
        """Track group/chat information."""
        group_data = {
            'id': chat.id,
            'type': chat.type,
            'title': chat.title,
            'username': chat.username,
            'description': chat.description,
            'last_active': __import__('datetime').datetime.now()
        }
        
        await create_or_update_group(group_data)