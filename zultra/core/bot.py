"""
Production-ready main bot class for Zultra Telegram Bot.
Bulletproof bot initialization, lifecycle management, and error handling.
"""

import asyncio
import signal
import sys
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

from telegram import Update, Bot
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, MessageHandler, 
    CallbackQueryHandler, InlineQueryHandler, filters
)
from telegram.error import TelegramError, NetworkError, TimedOut
from loguru import logger

from .config import get_settings, get_runtime_config
from .errors import global_error_handler, BotError
from ..db.database import db_manager
from ..middlewares.base import BaseMiddleware


class BotInitializationError(Exception):
    """Bot initialization related errors."""
    pass


class ZultraBot:
    """Production-ready Telegram bot with comprehensive error handling."""
    
    def __init__(self):
        self.settings = get_settings()
        self.runtime_config = get_runtime_config()
        self.application: Optional[Application] = None
        self.is_initialized = False
        self.is_running = False
        self.shutdown_event = asyncio.Event()
        self.handlers = {}
        self.middlewares: List[BaseMiddleware] = []
        
    async def initialize(self) -> bool:
        """Initialize bot with comprehensive error handling."""
        logger.info("Initializing Zultra Bot...")
        
        try:
            # Initialize database first
            if not await self._initialize_database():
                raise BotInitializationError("Database initialization failed")
            
            # Create and configure application
            if not await self._create_application():
                raise BotInitializationError("Application creation failed")
            
            # Setup error handling
            self._setup_error_handling()
            
            # Initialize middlewares
            if not await self._initialize_middlewares():
                raise BotInitializationError("Middleware initialization failed")
            
            # Setup command handlers
            if not await self._setup_handlers():
                raise BotInitializationError("Handler setup failed")
            
            # Initialize services
            if not await self._initialize_services():
                logger.warning("Some services failed to initialize - continuing with limited functionality")
            
            # Validate bot configuration
            if not await self._validate_bot():
                raise BotInitializationError("Bot validation failed")
            
            self.is_initialized = True
            logger.success("Zultra Bot initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Bot initialization failed: {e}")
            await self._cleanup_on_failure()
            return False
    
    async def _initialize_database(self) -> bool:
        """Initialize database with retry logic."""
        logger.info("Initializing database...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                success = await db_manager.initialize()
                if success:
                    logger.success("Database initialized")
                    return True
                else:
                    logger.warning(f"Database initialization attempt {attempt + 1} failed")
                    
            except Exception as e:
                logger.error(f"Database initialization error: {e}")
                
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        logger.error("Database initialization failed after all retries")
        return False
    
    async def _create_application(self) -> bool:
        """Create and configure Telegram application."""
        try:
            logger.info("Creating Telegram application...")
            
            # Create application builder
            builder = ApplicationBuilder().token(self.settings.bot_token)
            
            # Configure application settings
            builder = builder.concurrent_updates(True)
            builder = builder.connection_pool_size(self.settings.connection_pool_size)
            builder = builder.pool_timeout(30.0)
            builder = builder.read_timeout(30.0)
            builder = builder.write_timeout(30.0)
            builder = builder.connect_timeout(30.0)
            
            # Build application
            self.application = builder.build()
            
            logger.success("Telegram application created")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create application: {e}")
            return False
    
    def _setup_error_handling(self) -> None:
        """Setup comprehensive error handling."""
        try:
            # Add global error handler
            self.application.add_error_handler(global_error_handler)
            
            # Setup signal handlers for graceful shutdown
            if sys.platform != "win32":
                signal.signal(signal.SIGTERM, self._signal_handler)
                signal.signal(signal.SIGINT, self._signal_handler)
            
            logger.info("Error handling configured")
            
        except Exception as e:
            logger.error(f"Failed to setup error handling: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_event.set()
    
    async def _initialize_middlewares(self) -> bool:
        """Initialize all middlewares."""
        try:
            logger.info("Initializing middlewares...")
            
            # Import middleware classes
            from ..middlewares import (
                LoggingMiddleware, UserMiddleware, RateLimitMiddleware,
                AntiSpamMiddleware, PermissionMiddleware
            )
            
            # Initialize middlewares in order
            middleware_classes = [
                LoggingMiddleware,
                UserMiddleware,
                RateLimitMiddleware,
                AntiSpamMiddleware,
                PermissionMiddleware
            ]
            
            for middleware_class in middleware_classes:
                try:
                    middleware = middleware_class()
                    self.middlewares.append(middleware)
                    logger.debug(f"Initialized {middleware_class.__name__}")
                except Exception as e:
                    logger.error(f"Failed to initialize {middleware_class.__name__}: {e}")
                    return False
            
            logger.success(f"Initialized {len(self.middlewares)} middlewares")
            return True
            
        except Exception as e:
            logger.error(f"Middleware initialization failed: {e}")
            return False
    
    async def _setup_handlers(self) -> bool:
        """Setup all command and message handlers."""
        try:
            logger.info("Setting up handlers...")
            
            # Import handler classes
            from ..handlers import (
                CoreHandlers, FunHandlers, AIHandlers,
                UtilityHandlers, AdminHandlers, AIControlHandlers
            )
            
            # Initialize handlers
            self.handlers = {
                'core': CoreHandlers(),
                'fun': FunHandlers(),
                'ai': AIHandlers(),
                'utility': UtilityHandlers(),
                'admin': AdminHandlers(),
                'ai_control': AIControlHandlers()
            }
            
            # Register command handlers
            await self._register_command_handlers()
            
            # Register message handlers
            await self._register_message_handlers()
            
            # Register callback handlers
            await self._register_callback_handlers()
            
            logger.success("All handlers registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Handler setup failed: {e}")
            return False
    
    async def _register_command_handlers(self) -> None:
        """Register all command handlers with error wrapping."""
        app = self.application
        
        # Core commands
        app.add_handler(CommandHandler("start", self._wrap_handler(self.handlers['core'].start_command)))
        app.add_handler(CommandHandler("help", self._wrap_handler(self.handlers['core'].help_command)))
        app.add_handler(CommandHandler("settings", self._wrap_handler(self.handlers['core'].settings_command)))
        app.add_handler(CommandHandler("about", self._wrap_handler(self.handlers['core'].about_command)))
        app.add_handler(CommandHandler("uptime", self._wrap_handler(self.handlers['core'].uptime_command)))
        app.add_handler(CommandHandler("ping", self._wrap_handler(self.handlers['core'].ping_command)))
        
        # Fun commands
        app.add_handler(CommandHandler("truth", self._wrap_handler(self.handlers['fun'].truth_command)))
        app.add_handler(CommandHandler("dare", self._wrap_handler(self.handlers['fun'].dare_command)))
        app.add_handler(CommandHandler("8ball", self._wrap_handler(self.handlers['fun'].eightball_command)))
        app.add_handler(CommandHandler("quote", self._wrap_handler(self.handlers['fun'].quote_command)))
        app.add_handler(CommandHandler("roast", self._wrap_handler(self.handlers['fun'].roast_command)))
        app.add_handler(CommandHandler("ship", self._wrap_handler(self.handlers['fun'].ship_command)))
        
        # Utility commands
        app.add_handler(CommandHandler("id", self._wrap_handler(self.handlers['utility'].id_command)))
        app.add_handler(CommandHandler("userinfo", self._wrap_handler(self.handlers['utility'].userinfo_command)))
        app.add_handler(CommandHandler("stats", self._wrap_handler(self.handlers['utility'].stats_command)))
        app.add_handler(CommandHandler("calc", self._wrap_handler(self.handlers['utility'].calc_command)))
        app.add_handler(CommandHandler("time", self._wrap_handler(self.handlers['utility'].time_command)))
        app.add_handler(CommandHandler("invite", self._wrap_handler(self.handlers['utility'].invite_command)))
        
        # AI commands
        app.add_handler(CommandHandler("ask", self._wrap_handler(self.handlers['ai'].ask_command)))
        app.add_handler(CommandHandler("translate", self._wrap_handler(self.handlers['ai'].translate_command)))
        app.add_handler(CommandHandler("ocr", self._wrap_handler(self.handlers['ai'].ocr_command)))
        app.add_handler(CommandHandler("imagegen", self._wrap_handler(self.handlers['ai'].imagegen_command)))
        
        # Admin commands (with permission checking)
        app.add_handler(CommandHandler("ban", self._wrap_admin_handler(self.handlers['admin'].ban_command)))
        app.add_handler(CommandHandler("kick", self._wrap_admin_handler(self.handlers['admin'].kick_command)))
        app.add_handler(CommandHandler("mute", self._wrap_admin_handler(self.handlers['admin'].mute_command)))
        app.add_handler(CommandHandler("warn", self._wrap_admin_handler(self.handlers['admin'].warn_command)))
        
        # AI control commands
        app.add_handler(CommandHandler("setai", self._wrap_handler(self.handlers['ai_control'].setai_command)))
        app.add_handler(CommandHandler("aiusage", self._wrap_handler(self.handlers['ai_control'].aiusage_command)))
        
        logger.debug("Command handlers registered")
    
    async def _register_message_handlers(self) -> None:
        """Register message handlers."""
        app = self.application
        
        # Text messages (non-commands)
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self._wrap_handler(self._handle_text_message)
        ))
        
        # Photo messages
        app.add_handler(MessageHandler(
            filters.PHOTO, 
            self._wrap_handler(self._handle_photo_message)
        ))
        
        # New member events
        app.add_handler(MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            self._wrap_handler(self._handle_new_member)
        ))
        
        logger.debug("Message handlers registered")
    
    async def _register_callback_handlers(self) -> None:
        """Register callback query handlers."""
        app = self.application
        
        # Callback queries
        app.add_handler(CallbackQueryHandler(self._wrap_handler(self._handle_callback_query)))
        
        # Inline queries
        app.add_handler(InlineQueryHandler(self._wrap_handler(self._handle_inline_query)))
        
        logger.debug("Callback handlers registered")
    
    def _wrap_handler(self, handler_func):
        """Wrap handler function with middleware and error handling."""
        async def wrapped_handler(update: Update, context):
            try:
                # Process through middlewares
                for middleware in self.middlewares:
                    if middleware.is_enabled():
                        should_continue = await middleware.process_update(update, context)
                        if not should_continue:
                            return
                
                # Execute the actual handler
                await handler_func(update, context)
                
                # Post-process through middlewares
                for middleware in reversed(self.middlewares):
                    if middleware.is_enabled():
                        await middleware.post_process(update, context)
                        
            except BotError as e:
                logger.error(f"Bot error in handler: {e}")
                await self._send_error_message(update, e.user_message)
                
            except Exception as e:
                logger.exception(f"Unexpected error in handler: {e}")
                await self._send_error_message(update, "An unexpected error occurred. Please try again.")
        
        return wrapped_handler
    
    def _wrap_admin_handler(self, handler_func):
        """Wrap admin handler with permission checking."""
        async def wrapped_admin_handler(update: Update, context):
            user_id = update.effective_user.id
            
            # Check if user is owner or admin
            if (user_id not in self.settings.get_owner_ids() and 
                user_id not in self.settings.get_admin_ids()):
                await update.message.reply_text("❌ You don't have permission to use this command.")
                return
            
            # Process normally
            await self._wrap_handler(handler_func)(update, context)
        
        return wrapped_admin_handler
    
    async def _send_error_message(self, update: Update, message: str):
        """Send error message safely."""
        try:
            if update.message:
                await update.message.reply_text(f"❌ {message}")
            elif update.callback_query:
                await update.callback_query.answer(f"❌ {message}", show_alert=True)
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    
    async def _initialize_services(self) -> bool:
        """Initialize external services."""
        try:
            logger.info("Initializing services...")
            
            # Initialize AI service (if available)
            try:
                from ..services import AIOrchestrator
                self.ai_orchestrator = AIOrchestrator()
                await self.ai_orchestrator.initialize()
                logger.info("AI orchestrator initialized")
            except Exception as e:
                logger.warning(f"AI orchestrator initialization failed: {e}")
            
            # Initialize Redis cache (if available)
            if self.settings.redis_url:
                try:
                    import redis.asyncio as redis
                    self.redis = redis.from_url(self.settings.redis_url)
                    await self.redis.ping()
                    logger.info("Redis cache initialized")
                except Exception as e:
                    logger.warning(f"Redis initialization failed: {e}")
                    self.redis = None
            else:
                self.redis = None
            
            logger.success("Services initialization completed")
            return True
            
        except Exception as e:
            logger.error(f"Services initialization failed: {e}")
            return False
    
    async def _validate_bot(self) -> bool:
        """Validate bot configuration and connectivity."""
        try:
            logger.info("Validating bot configuration...")
            
            # Test bot token
            bot = Bot(self.settings.bot_token)
            bot_info = await bot.get_me()
            logger.info(f"Bot validated: @{bot_info.username} ({bot_info.first_name})")
            
            # Store bot info
            self.bot_info = bot_info
            
            return True
            
        except TelegramError as e:
            logger.error(f"Bot validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected validation error: {e}")
            return False
    
    async def start(self, use_webhook: bool = False) -> None:
        """Start the bot with comprehensive error handling."""
        if not self.is_initialized:
            logger.error("Bot not initialized. Call initialize() first.")
            return
        
        try:
            logger.info("Starting Zultra Bot...")
            self.is_running = True
            
            if use_webhook and self.settings.bot_webhook_url:
                await self._start_webhook()
            else:
                await self._start_polling()
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
        finally:
            await self.shutdown()
    
    async def _start_polling(self) -> None:
        """Start bot with polling mode."""
        try:
            logger.info("Starting polling mode...")
            
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES
            )
            
            logger.success("Bot is running in polling mode")
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"Polling mode error: {e}")
            raise
        finally:
            if self.application and self.application.updater:
                await self.application.updater.stop()
                await self.application.stop()
    
    async def _start_webhook(self) -> None:
        """Start bot with webhook mode."""
        try:
            logger.info("Starting webhook mode...")
            
            await self.application.initialize()
            await self.application.start()
            
            await self.application.updater.start_webhook(
                listen=self.settings.webhook_host,
                port=self.settings.webhook_port,
                url_path=self.settings.webhook_path,
                webhook_url=self.settings.bot_webhook_url,
                drop_pending_updates=True
            )
            
            logger.success(f"Bot is running in webhook mode: {self.settings.bot_webhook_url}")
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"Webhook mode error: {e}")
            raise
        finally:
            if self.application and self.application.updater:
                await self.application.updater.stop()
                await self.application.stop()
    
    async def shutdown(self) -> None:
        """Graceful shutdown with cleanup."""
        if not self.is_running:
            return
        
        logger.info("Shutting down Zultra Bot...")
        self.is_running = False
        
        try:
            # Stop the application
            if self.application:
                await self.application.shutdown()
                logger.info("Application shutdown complete")
            
            # Close database connections
            await db_manager.close()
            logger.info("Database connections closed")
            
            # Close Redis connection
            if hasattr(self, 'redis') and self.redis:
                await self.redis.close()
                logger.info("Redis connection closed")
            
            # Signal shutdown complete
            self.shutdown_event.set()
            logger.success("Zultra Bot shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def _cleanup_on_failure(self) -> None:
        """Cleanup resources on initialization failure."""
        try:
            if hasattr(self, 'application') and self.application:
                await self.application.shutdown()
            
            await db_manager.close()
            
            if hasattr(self, 'redis') and self.redis:
                await self.redis.close()
                
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    # Message handler implementations
    async def _handle_text_message(self, update: Update, context):
        """Handle text messages."""
        # Check for AFK mentions, auto-responses, etc.
        pass
    
    async def _handle_photo_message(self, update: Update, context):
        """Handle photo messages."""
        # Can be used for OCR or image analysis
        pass
    
    async def _handle_new_member(self, update: Update, context):
        """Handle new member events."""
        # Welcome messages, captcha, etc.
        pass
    
    async def _handle_callback_query(self, update: Update, context):
        """Handle callback queries."""
        query = update.callback_query
        await query.answer()
        # Handle inline keyboard callbacks
    
    async def _handle_inline_query(self, update: Update, context):
        """Handle inline queries."""
        # Handle inline bot queries
        pass
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive bot health status."""
        return {
            "bot": {
                "initialized": self.is_initialized,
                "running": self.is_running,
                "handlers_count": len(self.handlers),
                "middlewares_count": len(self.middlewares)
            },
            "database": db_manager.health_check() if db_manager.is_initialized else {"status": "not_initialized"},
            "config": self.settings.dict() if hasattr(self.settings, 'dict') else str(self.settings),
            "runtime": {
                "uptime": self.get_uptime(),
                "version": self.runtime_config.version
            }
        }
    
    def get_uptime(self) -> str:
        """Get bot uptime."""
        if not hasattr(self.runtime_config, 'start_time'):
            return "Unknown"
        
        uptime_seconds = __import__('time').time() - self.runtime_config.start_time
        return f"{uptime_seconds:.0f}s"