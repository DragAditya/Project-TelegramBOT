"""
Permission middleware for Zultra Telegram Bot.
Handles user permissions and access control.
"""

from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from .base import BaseMiddleware
from ..core.config import get_settings


class PermissionMiddleware(BaseMiddleware):
    """Middleware for permission checking."""
    
    def __init__(self):
        super().__init__("PermissionMiddleware")
        self.settings = get_settings()
    
    async def _process_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check user permissions."""
        if not update.effective_user:
            return True
        
        user_id = update.effective_user.id
        
        # Store user permission level in context
        context.user_data = context.user_data or {}
        
        if user_id in self.settings.get_owner_ids():
            context.user_data['permission_level'] = 'owner'
        elif user_id in self.settings.get_admin_ids():
            context.user_data['permission_level'] = 'admin'
        else:
            context.user_data['permission_level'] = 'user'
        
        return True