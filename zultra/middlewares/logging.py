"""
Logging middleware for Zultra Telegram Bot.
Handles comprehensive logging of all bot interactions.
"""

import time
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from .base import BaseMiddleware


class LoggingMiddleware(BaseMiddleware):
    """Middleware for logging all bot interactions."""
    
    def __init__(self):
        super().__init__("LoggingMiddleware")
        self.log_level = "INFO"
    
    async def process_update(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """Process and log the update."""
        if not self.enabled:
            return True
        
        start_time = time.time()
        
        # Store start time in context for response time calculation
        context.user_data = context.user_data or {}
        context.user_data['_request_start'] = start_time
        
        await self._log_incoming_update(update, context)
        
        return True
    
    async def post_process(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Log the completion of update processing."""
        if not self.enabled:
            return
        
        # Calculate response time
        start_time = context.user_data.get('_request_start', time.time())
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        await self._log_response(update, context, response_time)
    
    async def _log_incoming_update(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Log incoming update details."""
        user_id = self.get_user_id(update)
        chat_id = self.get_chat_id(update)
        
        # Determine update type
        update_type = self._get_update_type(update)
        
        # Get message content (truncated for logging)
        content = self._get_update_content(update)
        
        # Get user info
        user_info = self._get_user_info(update)
        
        # Get chat info
        chat_info = self._get_chat_info(update)
        
        # Log the incoming request
        logger.info(
            f"Incoming {update_type}",
            extra={
                "update_type": update_type,
                "user_id": user_id,
                "chat_id": chat_id,
                "content": content,
                "user_info": user_info,
                "chat_info": chat_info,
                "update_id": update.update_id
            }
        )
    
    async def _log_response(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE,
        response_time: float
    ) -> None:
        """Log response details."""
        user_id = self.get_user_id(update)
        chat_id = self.get_chat_id(update)
        
        logger.info(
            f"Request processed in {response_time:.2f}ms",
            extra={
                "user_id": user_id,
                "chat_id": chat_id,
                "response_time_ms": response_time,
                "update_id": update.update_id
            }
        )
    
    def _get_update_type(self, update: Update) -> str:
        """Determine the type of update."""
        if update.message:
            if update.message.text and update.message.text.startswith('/'):
                return "command"
            elif update.message.text:
                return "text_message"
            elif update.message.photo:
                return "photo"
            elif update.message.document:
                return "document"
            elif update.message.voice:
                return "voice"
            elif update.message.video:
                return "video"
            elif update.message.sticker:
                return "sticker"
            elif update.message.new_chat_members:
                return "new_member"
            elif update.message.left_chat_member:
                return "left_member"
            else:
                return "message"
        elif update.callback_query:
            return "callback_query"
        elif update.inline_query:
            return "inline_query"
        elif update.edited_message:
            return "edited_message"
        elif update.channel_post:
            return "channel_post"
        elif update.edited_channel_post:
            return "edited_channel_post"
        else:
            return "unknown"
    
    def _get_update_content(self, update: Update) -> Optional[str]:
        """Get the content of the update (truncated)."""
        content = None
        
        if update.message:
            if update.message.text:
                content = update.message.text
            elif update.message.caption:
                content = f"[Media] {update.message.caption}"
            else:
                content = "[Media without caption]"
        elif update.callback_query:
            content = f"[Callback] {update.callback_query.data}"
        elif update.inline_query:
            content = f"[Inline] {update.inline_query.query}"
        elif update.edited_message and update.edited_message.text:
            content = f"[Edited] {update.edited_message.text}"
        
        # Truncate long content
        if content and len(content) > 200:
            content = content[:200] + "..."
        
        return content
    
    def _get_user_info(self, update: Update) -> Optional[dict]:
        """Get user information from update."""
        user = update.effective_user
        if not user:
            return None
        
        return {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_bot": user.is_bot,
            "language_code": user.language_code
        }
    
    def _get_chat_info(self, update: Update) -> Optional[dict]:
        """Get chat information from update."""
        chat = update.effective_chat
        if not chat:
            return None
        
        chat_info = {
            "id": chat.id,
            "type": chat.type
        }
        
        if chat.title:
            chat_info["title"] = chat.title
        if chat.username:
            chat_info["username"] = chat.username
        
        return chat_info
    
    def set_log_level(self, level: str) -> None:
        """Set the logging level."""
        self.log_level = level.upper()
        logger.info(f"Logging middleware level set to {self.log_level}")
    
    async def log_command_execution(
        self, 
        command: str, 
        user_id: int, 
        chat_id: int, 
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """Log command execution details."""
        if success:
            logger.info(
                f"Command /{command} executed successfully",
                extra={
                    "command": command,
                    "user_id": user_id,
                    "chat_id": chat_id,
                    "success": True
                }
            )
        else:
            logger.warning(
                f"Command /{command} failed: {error}",
                extra={
                    "command": command,
                    "user_id": user_id,
                    "chat_id": chat_id,
                    "success": False,
                    "error": error
                }
            )
    
    async def log_ai_request(
        self, 
        provider: str, 
        model: str, 
        user_id: int, 
        chat_id: int,
        tokens_used: int = 0,
        cost: float = 0.0,
        response_time: float = 0.0
    ) -> None:
        """Log AI request details."""
        logger.info(
            f"AI request to {provider}/{model}",
            extra={
                "ai_provider": provider,
                "ai_model": model,
                "user_id": user_id,
                "chat_id": chat_id,
                "tokens_used": tokens_used,
                "cost": cost,
                "response_time": response_time
            }
        )
    
    async def log_moderation_action(
        self, 
        action: str, 
        moderator_id: int, 
        target_user_id: int, 
        chat_id: int,
        reason: Optional[str] = None
    ) -> None:
        """Log moderation actions."""
        logger.warning(
            f"Moderation action: {action}",
            extra={
                "action": action,
                "moderator_id": moderator_id,
                "target_user_id": target_user_id,
                "chat_id": chat_id,
                "reason": reason
            }
        )
    
    async def log_security_event(
        self, 
        event_type: str, 
        user_id: int, 
        chat_id: int,
        details: Optional[dict] = None
    ) -> None:
        """Log security-related events."""
        logger.warning(
            f"Security event: {event_type}",
            extra={
                "event_type": event_type,
                "user_id": user_id,
                "chat_id": chat_id,
                "details": details or {}
            }
        )