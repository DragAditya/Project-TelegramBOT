"""
Production-ready error handling system for Zultra Telegram Bot.
Comprehensive error management with logging, recovery, and user feedback.
"""

import asyncio
import traceback
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Type
from enum import Enum

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import (
    TelegramError, NetworkError, BadRequest, TimedOut, 
    ChatMigrated, RetryAfter, Forbidden, Conflict
)
from loguru import logger


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better organization."""
    TELEGRAM_API = "telegram_api"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    VALIDATION = "validation"
    PERMISSION = "permission"
    RATE_LIMIT = "rate_limit"
    NETWORK = "network"
    UNKNOWN = "unknown"


class BotError(Exception):
    """Base exception for bot-related errors."""
    
    def __init__(
        self, 
        message: str, 
        user_message: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.user_message = user_message or "An error occurred. Please try again."
        self.severity = severity
        self.category = category
        self.metadata = metadata or {}
        self.timestamp = datetime.now()


class ConfigurationError(BotError):
    """Configuration related errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            user_message="Bot configuration error. Please contact an administrator.",
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.VALIDATION,
            **kwargs
        )


class DatabaseError(BotError):
    """Database related errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            user_message="Database error. Please try again later.",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DATABASE,
            **kwargs
        )


class PermissionError(BotError):
    """Permission related errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            user_message="You don't have permission to perform this action.",
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.PERMISSION,
            **kwargs
        )


class RateLimitError(BotError):
    """Rate limit related errors."""
    
    def __init__(self, message: str, retry_after: int = 60, **kwargs):
        super().__init__(
            message,
            user_message=f"Rate limit exceeded. Please try again in {retry_after} seconds.",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.RATE_LIMIT,
            metadata={"retry_after": retry_after},
            **kwargs
        )


class ExternalAPIError(BotError):
    """External API related errors."""
    
    def __init__(self, message: str, api_name: str = "External API", **kwargs):
        super().__init__(
            message,
            user_message=f"{api_name} is currently unavailable. Please try again later.",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.EXTERNAL_API,
            metadata={"api_name": api_name},
            **kwargs
        )


class ValidationError(BotError):
    """Input validation errors."""
    
    def __init__(self, message: str, field: str = None, **kwargs):
        super().__init__(
            message,
            user_message="Invalid input. Please check your data and try again.",
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.VALIDATION,
            metadata={"field": field} if field else {},
            **kwargs
        )


class NetworkError(BotError):
    """Network related errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            user_message="Network error. Please check your connection and try again.",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.NETWORK,
            **kwargs
        )


class ErrorTracker:
    """Track and analyze bot errors."""
    
    def __init__(self, max_errors: int = 1000):
        self.errors: List[Dict[str, Any]] = []
        self.max_errors = max_errors
        self.error_counts = {}
        self.start_time = datetime.now()
    
    def track_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Track an error occurrence."""
        error_data = {
            "timestamp": datetime.now(),
            "error_type": type(error).__name__,
            "message": str(error),
            "context": context or {},
            "traceback": traceback.format_exc()
        }
        
        # Add to errors list
        self.errors.append(error_data)
        
        # Maintain max errors limit
        if len(self.errors) > self.max_errors:
            self.errors.pop(0)
        
        # Update error counts
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Log based on severity
        if isinstance(error, BotError):
            if error.severity == ErrorSeverity.CRITICAL:
                logger.critical(f"CRITICAL ERROR: {error.message}")
            elif error.severity == ErrorSeverity.HIGH:
                logger.error(f"HIGH SEVERITY: {error.message}")
            elif error.severity == ErrorSeverity.MEDIUM:
                logger.warning(f"MEDIUM SEVERITY: {error.message}")
            else:
                logger.info(f"LOW SEVERITY: {error.message}")
        else:
            logger.error(f"Unhandled error: {error}")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        total_errors = len(self.errors)
        runtime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
        
        return {
            "total_errors": total_errors,
            "errors_per_hour": round(total_errors / max(runtime_hours, 1), 2),
            "error_counts": self.error_counts.copy(),
            "recent_errors": self.errors[-10:] if self.errors else [],
            "most_common_error": max(self.error_counts.items(), key=lambda x: x[1])[0] if self.error_counts else None
        }
    
    def get_critical_errors(self) -> List[Dict[str, Any]]:
        """Get critical errors from the last 24 hours."""
        cutoff_time = datetime.now() - timedelta(hours=24)
        return [
            error for error in self.errors 
            if error["timestamp"] >= cutoff_time and "CRITICAL" in error["message"]
        ]


# Global error tracker
error_tracker = ErrorTracker()


def classify_telegram_error(error: TelegramError) -> ErrorCategory:
    """Classify Telegram errors into categories."""
    if isinstance(error, BadRequest):
        return ErrorCategory.VALIDATION
    elif isinstance(error, Forbidden):
        return ErrorCategory.PERMISSION
    elif isinstance(error, RetryAfter):
        return ErrorCategory.RATE_LIMIT
    elif isinstance(error, (NetworkError, TimedOut)):
        return ErrorCategory.NETWORK
    elif isinstance(error, ChatMigrated):
        return ErrorCategory.TELEGRAM_API
    else:
        return ErrorCategory.TELEGRAM_API


async def handle_telegram_error(error: TelegramError, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handle Telegram-specific errors with appropriate responses."""
    try:
        error_category = classify_telegram_error(error)
        
        # Handle specific error types
        if isinstance(error, BadRequest):
            await _handle_bad_request(error, update, context)
        elif isinstance(error, Forbidden):
            await _handle_forbidden(error, update, context)
        elif isinstance(error, RetryAfter):
            await _handle_retry_after(error, update, context)
        elif isinstance(error, TimedOut):
            await _handle_timeout(error, update, context)
        elif isinstance(error, ChatMigrated):
            await _handle_chat_migrated(error, update, context)
        elif isinstance(error, NetworkError):
            await _handle_network_error(error, update, context)
        else:
            await _handle_generic_telegram_error(error, update, context)
        
        return True
        
    except Exception as e:
        logger.error(f"Error handling Telegram error: {e}")
        return False


async def _handle_bad_request(error: BadRequest, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle BadRequest errors."""
    error_msg = str(error).lower()
    
    if "message not found" in error_msg:
        # Message was deleted or doesn't exist
        logger.warning(f"Message not found: {error}")
        return
    
    if "chat not found" in error_msg:
        # Chat doesn't exist or bot was removed
        logger.warning(f"Chat not found: {error}")
        return
    
    if "message is too long" in error_msg:
        # Message exceeds length limit
        if update.message:
            await update.message.reply_text(
                "❌ Message is too long. Please use a shorter message."
            )
        return
    
    if "file is too big" in error_msg:
        # File size exceeds limit
        if update.message:
            await update.message.reply_text(
                "❌ File is too large. Please use a smaller file."
            )
        return
    
    # Generic bad request
    logger.warning(f"Bad request: {error}")
    if update.message:
        await update.message.reply_text(
            "❌ Invalid request. Please check your input and try again."
        )


async def _handle_forbidden(error: Forbidden, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Forbidden errors."""
    error_msg = str(error).lower()
    
    if "bot was blocked by the user" in error_msg:
        logger.info(f"Bot blocked by user {update.effective_user.id}")
        # Remove user from database or mark as inactive
        return
    
    if "not enough rights" in error_msg:
        logger.warning(f"Insufficient bot permissions: {error}")
        if update.message:
            await update.message.reply_text(
                "❌ I don't have enough permissions to perform this action."
            )
        return
    
    logger.warning(f"Forbidden access: {error}")


async def _handle_retry_after(error: RetryAfter, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle RetryAfter errors (rate limiting)."""
    retry_after = error.retry_after
    logger.warning(f"Rate limited for {retry_after} seconds")
    
    if update.message:
        await update.message.reply_text(
            f"⏳ Rate limit exceeded. Please try again in {retry_after} seconds."
        )
    
    # Schedule retry if appropriate
    if context.job_queue:
        context.job_queue.run_once(
            lambda ctx: logger.info("Rate limit period ended"),
            retry_after
        )


async def _handle_timeout(error: TimedOut, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle timeout errors."""
    logger.warning(f"Request timed out: {error}")
    
    if update.message:
        await update.message.reply_text(
            "⏱️ Request timed out. Please try again."
        )


async def _handle_chat_migrated(error: ChatMigrated, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle chat migration."""
    old_chat_id = update.effective_chat.id
    new_chat_id = error.new_chat_id
    
    logger.info(f"Chat migrated from {old_chat_id} to {new_chat_id}")
    
    # Update chat ID in database
    # This would typically involve updating the group record
    # await update_chat_id(old_chat_id, new_chat_id)


async def _handle_network_error(error: NetworkError, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle network errors."""
    logger.warning(f"Network error: {error}")
    
    if update.message:
        await update.message.reply_text(
            "🌐 Network error. Please check your connection and try again."
        )


async def _handle_generic_telegram_error(error: TelegramError, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle generic Telegram errors."""
    logger.error(f"Unhandled Telegram error: {error}")
    
    if update.message:
        await update.message.reply_text(
            "❌ An error occurred while processing your request. Please try again."
        )


async def global_error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler for the bot."""
    error = context.error
    
    # Track the error
    error_context = {
        "update_id": update.update_id if update else None,
        "user_id": update.effective_user.id if update and update.effective_user else None,
        "chat_id": update.effective_chat.id if update and update.effective_chat else None,
        "command": update.message.text if update and update.message else None
    }
    
    error_tracker.track_error(error, error_context)
    
    try:
        # Handle Telegram-specific errors
        if isinstance(error, TelegramError):
            success = await handle_telegram_error(error, update, context)
            if success:
                return
        
        # Handle custom bot errors
        if isinstance(error, BotError):
            await _handle_bot_error(error, update, context)
            return
        
        # Handle unexpected errors
        await _handle_unexpected_error(error, update, context)
        
    except Exception as e:
        logger.critical(f"Error in error handler: {e}")
        await _send_fallback_error_message(update)


async def _handle_bot_error(error: BotError, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom bot errors."""
    logger.error(f"Bot error ({error.category.value}): {error.message}")
    
    try:
        if update.message:
            await update.message.reply_text(f"❌ {error.user_message}")
        elif update.callback_query:
            await update.callback_query.answer(f"❌ {error.user_message}", show_alert=True)
    except Exception as e:
        logger.error(f"Failed to send bot error message: {e}")


async def _handle_unexpected_error(error: Exception, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unexpected errors."""
    logger.exception(f"Unexpected error: {error}")
    
    # Send user-friendly message
    try:
        if update.message:
            await update.message.reply_text(
                "❌ An unexpected error occurred. The issue has been logged and will be investigated."
            )
        elif update.callback_query:
            await update.callback_query.answer(
                "❌ An unexpected error occurred. Please try again.",
                show_alert=True
            )
    except Exception as e:
        logger.error(f"Failed to send unexpected error message: {e}")


async def _send_fallback_error_message(update: Update):
    """Send fallback error message when all else fails."""
    try:
        if update and update.message:
            await update.message.reply_text("❌ System error. Please try again later.")
    except Exception:
        # Even fallback failed - just log it
        logger.critical("Complete error handling failure")


class ErrorRecovery:
    """Error recovery utilities."""
    
    @staticmethod
    async def retry_with_backoff(
        func,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0
    ):
        """Retry a function with exponential backoff."""
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                
                delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                logger.warning(f"Retry {attempt + 1}/{max_retries} failed: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
    
    @staticmethod
    async def with_circuit_breaker(
        func,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception
    ):
        """Execute function with circuit breaker pattern."""
        # This would typically be implemented with a proper circuit breaker
        # For now, just a simple wrapper
        try:
            return await func()
        except expected_exception as e:
            logger.warning(f"Circuit breaker triggered: {e}")
            raise


def setup_error_handling():
    """Setup error handling system."""
    logger.info("Error handling system initialized")
    
    # Setup uncaught exception handler
    import sys
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    sys.excepthook = handle_exception