"""
Logging middleware for Zultra Telegram Bot.
Provides comprehensive request/response logging and monitoring.
"""

import time
from typing import Dict, Any, Optional
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from .base import BaseMiddleware


class LoggingMiddleware(BaseMiddleware):
    """Middleware for logging all bot interactions."""
    
    def __init__(self):
        super().__init__("LoggingMiddleware")
        self.request_counter = 0
        self.slow_requests = []
        self.slow_request_threshold = 5.0  # seconds
    
    async def _process_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Log incoming requests."""
        self.request_counter += 1
        
        # Extract request information
        request_info = self._extract_request_info(update)
        
        # Store timing information
        context.bot_data['request_start_time'] = time.time()
        context.bot_data['request_id'] = self.request_counter
        
        # Log the request
        logger.info(
            f"[{self.request_counter}] {request_info['type']}: {request_info['summary']}",
            extra={
                'request_id': self.request_counter,
                'user_id': request_info.get('user_id'),
                'chat_id': request_info.get('chat_id'),
                'command': request_info.get('command'),
                'chat_type': request_info.get('chat_type')
            }
        )
        
        return True
    
    async def _post_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log request completion and timing."""
        start_time = context.bot_data.get('request_start_time')
        request_id = context.bot_data.get('request_id')
        
        if start_time and request_id:
            duration = time.time() - start_time
            
            # Log slow requests
            if duration > self.slow_request_threshold:
                self.slow_requests.append({
                    'request_id': request_id,
                    'duration': duration,
                    'timestamp': time.time()
                })
                
                # Keep only last 100 slow requests
                if len(self.slow_requests) > 100:
                    self.slow_requests.pop(0)
                
                logger.warning(
                    f"[{request_id}] SLOW REQUEST: {duration:.2f}s",
                    extra={'request_id': request_id, 'duration': duration}
                )
            else:
                logger.debug(
                    f"[{request_id}] Completed in {duration:.2f}s",
                    extra={'request_id': request_id, 'duration': duration}
                )
    
    def _extract_request_info(self, update: Update) -> Dict[str, Any]:
        """Extract relevant information from update."""
        info = {
            'type': 'unknown',
            'summary': 'Unknown update',
            'user_id': None,
            'chat_id': None,
            'command': None,
            'chat_type': None
        }
        
        # Extract basic info
        if update.effective_user:
            info['user_id'] = update.effective_user.id
        
        if update.effective_chat:
            info['chat_id'] = update.effective_chat.id
            info['chat_type'] = update.effective_chat.type
        
        # Determine update type and extract details
        if update.message:
            info['type'] = 'message'
            message = update.message
            
            if message.text:
                if message.text.startswith('/'):
                    info['type'] = 'command'
                    info['command'] = message.text.split()[0]
                    info['summary'] = f"Command: {info['command']}"
                else:
                    info['summary'] = f"Text: {message.text[:50]}..."
            
            elif message.photo:
                info['type'] = 'photo'
                info['summary'] = "Photo message"
            
            elif message.document:
                info['type'] = 'document'
                info['summary'] = f"Document: {message.document.file_name or 'Unknown'}"
            
            elif message.voice:
                info['type'] = 'voice'
                info['summary'] = "Voice message"
            
            elif message.video:
                info['type'] = 'video'
                info['summary'] = "Video message"
            
            elif message.sticker:
                info['type'] = 'sticker'
                info['summary'] = "Sticker message"
            
            else:
                info['summary'] = "Message (other type)"
        
        elif update.callback_query:
            info['type'] = 'callback_query'
            info['summary'] = f"Callback: {update.callback_query.data}"
        
        elif update.inline_query:
            info['type'] = 'inline_query'
            info['summary'] = f"Inline query: {update.inline_query.query}"
        
        elif update.edited_message:
            info['type'] = 'edited_message'
            info['summary'] = "Message edited"
        
        # Add user information if available
        if update.effective_user:
            user = update.effective_user
            user_info = f"@{user.username}" if user.username else f"ID:{user.id}"
            info['summary'] += f" from {user_info}"
        
        return info
    
    def get_stats(self) -> Dict[str, Any]:
        """Get detailed logging statistics."""
        base_stats = super().get_stats()
        
        # Add logging-specific stats
        base_stats.update({
            'total_requests': self.request_counter,
            'slow_requests_count': len(self.slow_requests),
            'slow_request_threshold': self.slow_request_threshold,
            'recent_slow_requests': self.slow_requests[-10:] if self.slow_requests else []
        })
        
        return base_stats