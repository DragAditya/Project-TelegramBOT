"""
Custom exceptions and error handling for Zultra Telegram Bot.
Provides structured error handling with proper logging and user feedback.
"""

from typing import Optional, Dict, Any
from loguru import logger


class BotError(Exception):
    """Base exception for all bot-related errors."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.user_message = user_message or "An error occurred. Please try again later."
        self.context = context or {}
        super().__init__(message)
    
    def log_error(self, user_id: Optional[int] = None, chat_id: Optional[int] = None):
        """Log the error with context."""
        context_info = {
            "error_code": self.error_code,
            "user_id": user_id,
            "chat_id": chat_id,
            **self.context
        }
        logger.error(f"{self.__class__.__name__}: {self.message}", extra=context_info)


class ValidationError(BotError):
    """Raised when user input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            user_message=f"Invalid input: {message}",
            context={"field": field},
            **kwargs
        )


class RateLimitError(BotError):
    """Raised when rate limits are exceeded."""
    
    def __init__(
        self, 
        limit_type: str, 
        retry_after: Optional[int] = None, 
        **kwargs
    ):
        message = f"Rate limit exceeded for {limit_type}"
        user_message = "You're sending messages too quickly. Please slow down."
        
        if retry_after:
            user_message += f" Try again in {retry_after} seconds."
        
        super().__init__(
            message=message,
            user_message=user_message,
            context={"limit_type": limit_type, "retry_after": retry_after},
            **kwargs
        )


class PermissionError(BotError):
    """Raised when user lacks required permissions."""
    
    def __init__(self, required_permission: str, **kwargs):
        super().__init__(
            message=f"Permission denied: requires {required_permission}",
            user_message="You don't have permission to use this command.",
            context={"required_permission": required_permission},
            **kwargs
        )


class DatabaseError(BotError):
    """Raised when database operations fail."""
    
    def __init__(self, operation: str, original_error: Optional[Exception] = None, **kwargs):
        message = f"Database error during {operation}"
        if original_error:
            message += f": {str(original_error)}"
        
        super().__init__(
            message=message,
            user_message="Database error occurred. Please try again later.",
            context={"operation": operation, "original_error": str(original_error) if original_error else None},
            **kwargs
        )


class AIProviderError(BotError):
    """Raised when AI provider requests fail."""
    
    def __init__(
        self, 
        provider: str, 
        reason: str, 
        is_quota_exceeded: bool = False,
        **kwargs
    ):
        message = f"AI provider {provider} error: {reason}"
        
        if is_quota_exceeded:
            user_message = f"AI service quota exceeded for {provider}. Please try later or use a different provider."
        else:
            user_message = f"AI service temporarily unavailable. Please try again later."
        
        super().__init__(
            message=message,
            user_message=user_message,
            context={"provider": provider, "reason": reason, "quota_exceeded": is_quota_exceeded},
            **kwargs
        )


class ConfigurationError(BotError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, config_key: str, **kwargs):
        super().__init__(
            message=f"Configuration error: {config_key}",
            user_message="Bot configuration error. Please contact an administrator.",
            context={"config_key": config_key},
            **kwargs
        )


class SpamDetectedError(BotError):
    """Raised when spam is detected."""
    
    def __init__(self, spam_type: str, **kwargs):
        super().__init__(
            message=f"Spam detected: {spam_type}",
            user_message="Your message appears to be spam and has been blocked.",
            context={"spam_type": spam_type},
            **kwargs
        )


class CaptchaError(BotError):
    """Raised when captcha verification fails."""
    
    def __init__(self, attempts_remaining: int = 0, **kwargs):
        message = "Captcha verification failed"
        user_message = "Captcha verification failed."
        
        if attempts_remaining > 0:
            user_message += f" You have {attempts_remaining} attempts remaining."
        else:
            user_message += " You will be removed from the group."
        
        super().__init__(
            message=message,
            user_message=user_message,
            context={"attempts_remaining": attempts_remaining},
            **kwargs
        )


class APIKeyError(BotError):
    """Raised when API key operations fail."""
    
    def __init__(self, operation: str, provider: Optional[str] = None, **kwargs):
        message = f"API key error: {operation}"
        if provider:
            message += f" for {provider}"
        
        super().__init__(
            message=message,
            user_message="API key error. Please check your configuration.",
            context={"operation": operation, "provider": provider},
            **kwargs
        )


# Error handler decorator
def handle_errors(log_errors: bool = True):
    """Decorator to handle exceptions in command handlers."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except BotError as e:
                if log_errors:
                    # Extract user and chat IDs from context if available
                    user_id = kwargs.get('user_id') or (args[0].from_user.id if len(args) > 0 and hasattr(args[0], 'from_user') else None)
                    chat_id = kwargs.get('chat_id') or (args[0].chat.id if len(args) > 0 and hasattr(args[0], 'chat') else None)
                    e.log_error(user_id=user_id, chat_id=chat_id)
                raise
            except Exception as e:
                if log_errors:
                    logger.exception(f"Unexpected error in {func.__name__}: {e}")
                
                # Convert to BotError
                raise BotError(
                    message=f"Unexpected error in {func.__name__}: {str(e)}",
                    error_code="UNEXPECTED_ERROR",
                    user_message="An unexpected error occurred. Please try again later."
                )
        
        return wrapper
    return decorator


# Global error handler for the bot
async def global_error_handler(update, context):
    """Global error handler for unhandled exceptions."""
    try:
        error = context.error
        
        # Log the error
        logger.exception(f"Unhandled error: {error}")
        
        # Try to send error message to user
        if update and update.effective_chat:
            try:
                if isinstance(error, BotError):
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"❌ {error.user_message}"
                    )
                else:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="❌ An unexpected error occurred. Please try again later."
                    )
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")
        
        # Report critical errors to admins
        if not isinstance(error, (RateLimitError, ValidationError, PermissionError)):
            await report_error_to_admins(context, error, update)
    
    except Exception as handler_error:
        logger.critical(f"Error in error handler: {handler_error}")


async def report_error_to_admins(context, error, update=None):
    """Report critical errors to bot administrators."""
    try:
        from ..core.config import get_settings
        settings = get_settings()
        
        error_message = f"🚨 **Critical Bot Error**\n\n"
        error_message += f"**Error Type:** {type(error).__name__}\n"
        error_message += f"**Message:** {str(error)}\n"
        
        if update:
            error_message += f"**User ID:** {update.effective_user.id if update.effective_user else 'Unknown'}\n"
            error_message += f"**Chat ID:** {update.effective_chat.id if update.effective_chat else 'Unknown'}\n"
            error_message += f"**Message:** {update.message.text if update.message else 'No message'}\n"
        
        # Send to owner IDs
        for owner_id in settings.owner_ids:
            try:
                await context.bot.send_message(
                    chat_id=owner_id,
                    text=error_message,
                    parse_mode='Markdown'
                )
            except Exception as send_error:
                logger.error(f"Failed to send error report to owner {owner_id}: {send_error}")
    
    except Exception as report_error:
        logger.error(f"Failed to report error to admins: {report_error}")


# Context manager for error handling
class ErrorContext:
    """Context manager for structured error handling."""
    
    def __init__(self, operation: str, user_id: Optional[int] = None, chat_id: Optional[int] = None):
        self.operation = operation
        self.user_id = user_id
        self.chat_id = chat_id
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and issubclass(exc_type, BotError):
            exc_val.log_error(user_id=self.user_id, chat_id=self.chat_id)
        elif exc_type:
            logger.exception(f"Error in {self.operation}")
            
        return False  # Don't suppress the exception