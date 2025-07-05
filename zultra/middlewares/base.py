"""
Base middleware class for Zultra Telegram Bot.
Provides foundation for all middleware implementations.
"""

import asyncio
from typing import Optional, Any, Dict
from abc import ABC, abstractmethod
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger


class BaseMiddleware(ABC):
    """Base class for all middleware implementations."""
    
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.enabled = True
        self.initialized = False
        self.stats = {
            'processed': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    async def initialize(self) -> bool:
        """Initialize middleware. Override in subclasses."""
        self.initialized = True
        logger.debug(f"Middleware {self.name} initialized")
        return True
    
    def enable(self) -> None:
        """Enable middleware."""
        self.enabled = True
        logger.debug(f"Middleware {self.name} enabled")
    
    def disable(self) -> None:
        """Disable middleware."""
        self.enabled = False
        logger.debug(f"Middleware {self.name} disabled")
    
    def is_enabled(self) -> bool:
        """Check if middleware is enabled."""
        return self.enabled and self.initialized
    
    async def process_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Process update through middleware.
        
        Returns:
            bool: True to continue processing, False to stop
        """
        if not self.is_enabled():
            return True
        
        try:
            self.stats['processed'] += 1
            return await self._process_update(update, context)
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error in middleware {self.name}: {e}")
            return True  # Continue processing by default
    
    async def post_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Post-process after handler execution."""
        if not self.is_enabled():
            return
        
        try:
            await self._post_process(update, context)
        except Exception as e:
            logger.error(f"Error in post-process middleware {self.name}: {e}")
    
    @abstractmethod
    async def _process_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Override this method in subclasses."""
        pass
    
    async def _post_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Override this method in subclasses if needed."""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get middleware statistics."""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'initialized': self.initialized,
            'processed': self.stats['processed'],
            'errors': self.stats['errors'],
            'error_rate': self.stats['errors'] / max(self.stats['processed'], 1),
            'uptime': (datetime.now() - self.stats['start_time']).total_seconds()
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', enabled={self.enabled})"