"""
Base middleware class for Zultra Telegram Bot.
Provides common functionality for all middleware components.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger


class BaseMiddleware(ABC):
    """Base class for all middleware components."""
    
    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__
        self.enabled = True
    
    @abstractmethod
    async def process_update(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """
        Process an update through the middleware.
        
        Args:
            update: The Telegram update
            context: The bot context
            
        Returns:
            bool: True to continue processing, False to stop
        """
        pass
    
    async def pre_process(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """
        Pre-process the update before main processing.
        Override in subclasses for custom behavior.
        
        Returns:
            bool: True to continue, False to stop processing
        """
        return True
    
    async def post_process(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Post-process the update after main processing.
        Override in subclasses for custom behavior.
        """
        pass
    
    def enable(self) -> None:
        """Enable the middleware."""
        self.enabled = True
        logger.info(f"Middleware {self.name} enabled")
    
    def disable(self) -> None:
        """Disable the middleware."""
        self.enabled = False
        logger.info(f"Middleware {self.name} disabled")
    
    def is_enabled(self) -> bool:
        """Check if middleware is enabled."""
        return self.enabled
    
    def get_user_id(self, update: Update) -> Optional[int]:
        """Extract user ID from update."""
        return update.effective_user.id if update.effective_user else None
    
    def get_chat_id(self, update: Update) -> Optional[int]:
        """Extract chat ID from update."""
        return update.effective_chat.id if update.effective_chat else None
    
    def get_message_text(self, update: Update) -> Optional[str]:
        """Extract message text from update."""
        if update.message:
            return update.message.text
        elif update.edited_message:
            return update.edited_message.text
        elif update.callback_query and update.callback_query.message:
            return update.callback_query.data
        return None
    
    def is_private_chat(self, update: Update) -> bool:
        """Check if the update is from a private chat."""
        return (
            update.effective_chat and 
            update.effective_chat.type == 'private'
        )
    
    def is_group_chat(self, update: Update) -> bool:
        """Check if the update is from a group chat."""
        return (
            update.effective_chat and 
            update.effective_chat.type in ['group', 'supergroup']
        )
    
    def is_channel(self, update: Update) -> bool:
        """Check if the update is from a channel."""
        return (
            update.effective_chat and 
            update.effective_chat.type == 'channel'
        )
    
    async def log_processing(
        self, 
        update: Update, 
        action: str, 
        details: Optional[str] = None
    ) -> None:
        """Log middleware processing."""
        user_id = self.get_user_id(update)
        chat_id = self.get_chat_id(update)
        
        log_msg = f"{self.name}: {action}"
        if details:
            log_msg += f" - {details}"
        
        logger.debug(
            log_msg,
            extra={
                "middleware": self.name,
                "user_id": user_id,
                "chat_id": chat_id,
                "action": action
            }
        )