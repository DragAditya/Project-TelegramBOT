"""
Main bot class for Zultra Telegram Bot.
Handles bot initialization, middleware setup, and lifecycle management.
"""

import asyncio
import signal
from datetime import datetime
from typing import Optional, Dict, Any
from telegram import Update
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, MessageHandler, 
    CallbackQueryHandler, InlineQueryHandler, filters
)
from loguru import logger

from .config import get_settings
from .errors import global_error_handler, ConfigurationError
from ..db import init_db, close_db, db_manager
from ..middlewares import (
    UserMiddleware, AntiSpamMiddleware, RateLimitMiddleware,
    LoggingMiddleware, PermissionMiddleware
)


class ZultraBot:
    """Main bot class for Zultra Telegram Bot."""
    
    def __init__(self):
        self.settings = get_settings()
        self.application: Optional[Application] = None
        self.start_time: Optional[datetime] = None
        self._shutdown_event = asyncio.Event()
        
    async def initialize(self) -> None:
        """Initialize the bot and all its components."""
        try:
            logger.info("Initializing Zultra Bot...")
            
            # Validate configuration
            await self._validate_config()
            
            # Initialize database
            await init_db()
            
            # Create application
            self.application = (
                ApplicationBuilder()
                .token(self.settings.bot_token)
                .concurrent_updates(True)
                .build()
            )
            
            # Setup error handling
            self.application.add_error_handler(global_error_handler)
            
            # Setup middlewares
            await self._setup_middlewares()
            
            # Setup handlers
            await self._setup_handlers()
            
            # Initialize services
            await self._initialize_services()
            
            self.start_time = datetime.now()
            logger.success("Zultra Bot initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            raise ConfigurationError(f"Bot initialization failed: {e}")
    
    async def start(self, use_webhook: bool = False) -> None:
        """Start the bot using polling or webhook."""
        if not self.application:
            raise RuntimeError("Bot not initialized. Call initialize() first.")
        
        try:
            if use_webhook and self.settings.bot_webhook_url:
                await self._start_webhook()
            else:
                await self._start_polling()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
        finally:
            await self.shutdown()
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the bot."""
        logger.info("Shutting down Zultra Bot...")
        
        try:
            if self.application:
                await self.application.shutdown()
                logger.info("Bot application shutdown complete")
            
            # Close database connections
            await close_db()
            logger.info("Database connections closed")
            
            # Signal shutdown complete
            self._shutdown_event.set()
            logger.success("Zultra Bot shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def _validate_config(self) -> None:
        """Validate bot configuration."""
        if not self.settings.bot_token:
            raise ConfigurationError("BOT_TOKEN is required")
        
        if self.settings.is_production:
            if not self.settings.bot_webhook_url:
                logger.warning("No webhook URL configured for production")
            
            if "sqlite" in self.settings.database_url:
                raise ConfigurationError("SQLite not recommended for production")
    
    async def _setup_middlewares(self) -> None:
        """Setup bot middlewares."""
        logger.info("Setting up middlewares...")
        
        # Logging middleware (first)
        logging_middleware = LoggingMiddleware()
        
        # User tracking middleware
        user_middleware = UserMiddleware()
        
        # Rate limiting middleware
        rate_limit_middleware = RateLimitMiddleware()
        
        # Anti-spam middleware
        anti_spam_middleware = AntiSpamMiddleware()
        
        # Permission middleware
        permission_middleware = PermissionMiddleware()
        
        # Add middlewares to application
        # Note: Order matters - logging should be first
        middlewares = [
            logging_middleware,
            user_middleware,
            rate_limit_middleware,
            anti_spam_middleware,
            permission_middleware
        ]
        
        # Store middlewares for access
        self.middlewares = {
            'logging': logging_middleware,
            'user': user_middleware,
            'rate_limit': rate_limit_middleware,
            'anti_spam': anti_spam_middleware,
            'permission': permission_middleware
        }
        
        logger.success("Middlewares setup complete")
    
    async def _setup_handlers(self) -> None:
        """Setup command and message handlers."""
        logger.info("Setting up handlers...")
        
        # Import handlers dynamically to avoid circular imports
        from ..handlers import (
            CoreHandlers, FunHandlers, AIHandlers, 
            UtilityHandlers, AdminHandlers, AIControlHandlers
        )
        
        # Initialize handler classes
        core_handlers = CoreHandlers()
        fun_handlers = FunHandlers()
        ai_handlers = AIHandlers()
        utility_handlers = UtilityHandlers()
        admin_handlers = AdminHandlers()
        ai_control_handlers = AIControlHandlers()
        
        # Store handlers for access
        self.handlers = {
            'core': core_handlers,
            'fun': fun_handlers,
            'ai': ai_handlers,
            'utility': utility_handlers,
            'admin': admin_handlers,
            'ai_control': ai_control_handlers
        }
        
        # Register all handlers
        await self._register_handlers()
        
        logger.success("Handlers setup complete")
    
    async def _register_handlers(self) -> None:
        """Register all command and message handlers."""
        app = self.application
        
        # Core commands
        app.add_handler(CommandHandler("start", self.handlers['core'].start_command))
        app.add_handler(CommandHandler("help", self.handlers['core'].help_command))
        app.add_handler(CommandHandler("settings", self.handlers['core'].settings_command))
        app.add_handler(CommandHandler("about", self.handlers['core'].about_command))
        app.add_handler(CommandHandler("uptime", self.handlers['core'].uptime_command))
        
        # Fun commands
        app.add_handler(CommandHandler("truth", self.handlers['fun'].truth_command))
        app.add_handler(CommandHandler("dare", self.handlers['fun'].dare_command))
        app.add_handler(CommandHandler("game", self.handlers['fun'].game_command))
        app.add_handler(CommandHandler("anime", self.handlers['fun'].anime_command))
        app.add_handler(CommandHandler("waifu", self.handlers['fun'].waifu_command))
        app.add_handler(CommandHandler("afk", self.handlers['fun'].afk_command))
        app.add_handler(CommandHandler("roast", self.handlers['fun'].roast_command))
        app.add_handler(CommandHandler("8ball", self.handlers['fun'].eightball_command))
        app.add_handler(CommandHandler("quote", self.handlers['fun'].quote_command))
        app.add_handler(CommandHandler("ship", self.handlers['fun'].ship_command))
        app.add_handler(CommandHandler("leaderboard", self.handlers['fun'].leaderboard_command))
        
        # AI commands
        app.add_handler(CommandHandler("ask", self.handlers['ai'].ask_command))
        app.add_handler(CommandHandler("translate", self.handlers['ai'].translate_command))
        app.add_handler(CommandHandler("ocr", self.handlers['ai'].ocr_command))
        app.add_handler(CommandHandler("imagegen", self.handlers['ai'].imagegen_command))
        
        # Utility commands
        app.add_handler(CommandHandler("id", self.handlers['utility'].id_command))
        app.add_handler(CommandHandler("userinfo", self.handlers['utility'].userinfo_command))
        app.add_handler(CommandHandler("stats", self.handlers['utility'].stats_command))
        app.add_handler(CommandHandler("ping", self.handlers['utility'].ping_command))
        app.add_handler(CommandHandler("invite", self.handlers['utility'].invite_command))
        app.add_handler(CommandHandler("shorten", self.handlers['utility'].shorten_command))
        app.add_handler(CommandHandler("weather", self.handlers['utility'].weather_command))
        app.add_handler(CommandHandler("calc", self.handlers['utility'].calc_command))
        app.add_handler(CommandHandler("convert", self.handlers['utility'].convert_command))
        app.add_handler(CommandHandler("time", self.handlers['utility'].time_command))
        app.add_handler(CommandHandler("whois", self.handlers['utility'].whois_command))
        app.add_handler(CommandHandler("paste", self.handlers['utility'].paste_command))
        
        # Admin commands
        app.add_handler(CommandHandler("ban", self.handlers['admin'].ban_command))
        app.add_handler(CommandHandler("kick", self.handlers['admin'].kick_command))
        app.add_handler(CommandHandler("mute", self.handlers['admin'].mute_command))
        app.add_handler(CommandHandler("warn", self.handlers['admin'].warn_command))
        app.add_handler(CommandHandler("purge", self.handlers['admin'].purge_command))
        app.add_handler(CommandHandler("del", self.handlers['admin'].delete_command))
        app.add_handler(CommandHandler("lock", self.handlers['admin'].lock_command))
        app.add_handler(CommandHandler("unlock", self.handlers['admin'].unlock_command))
        app.add_handler(CommandHandler("approve", self.handlers['admin'].approve_command))
        app.add_handler(CommandHandler("captcha", self.handlers['admin'].captcha_command))
        app.add_handler(CommandHandler("raidmode", self.handlers['admin'].raidmode_command))
        app.add_handler(CommandHandler("logs", self.handlers['admin'].logs_command))
        app.add_handler(CommandHandler("backups", self.handlers['admin'].backups_command))
        app.add_handler(CommandHandler("restore", self.handlers['admin'].restore_command))
        
        # AI Control commands
        app.add_handler(CommandHandler("setai", self.handlers['ai_control'].setai_command))
        app.add_handler(CommandHandler("aiusage", self.handlers['ai_control'].aiusage_command))
        
        # Callback query handlers
        app.add_handler(CallbackQueryHandler(self._handle_callback_query))
        
        # Message handlers
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        app.add_handler(MessageHandler(filters.PHOTO, self._handle_photo))
        app.add_handler(MessageHandler(filters.Document.IMAGE, self._handle_document))
        
        # Inline query handler
        app.add_handler(InlineQueryHandler(self._handle_inline_query))
        
        # New member handler
        app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, self._handle_new_member))
        
        # Left member handler
        app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, self._handle_left_member))
    
    async def _initialize_services(self) -> None:
        """Initialize bot services."""
        logger.info("Initializing services...")
        
        # Initialize AI orchestrator
        from ..services import AIOrchestrator
        self.ai_orchestrator = AIOrchestrator()
        await self.ai_orchestrator.initialize()
        
        # Initialize cache if Redis is available
        if self.settings.redis_url:
            try:
                import redis.asyncio as redis
                self.redis = redis.from_url(self.settings.redis_url)
                await self.redis.ping()
                logger.success("Redis cache initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis: {e}")
                self.redis = None
        else:
            self.redis = None
        
        logger.success("Services initialization complete")
    
    async def _start_polling(self) -> None:
        """Start bot using polling."""
        logger.info("Starting bot with polling...")
        
        # Initialize and start polling
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.success("Bot is running with polling mode")
        
        # Wait for shutdown signal
        await self._shutdown_event.wait()
        
        # Stop polling
        await self.application.updater.stop()
        await self.application.stop()
    
    async def _start_webhook(self) -> None:
        """Start bot using webhook."""
        logger.info("Starting bot with webhook...")
        
        # Initialize application
        await self.application.initialize()
        await self.application.start()
        
        # Start webhook
        await self.application.updater.start_webhook(
            listen=self.settings.webhook_host,
            port=self.settings.webhook_port,
            url_path=self.settings.webhook_path,
            webhook_url=self.settings.bot_webhook_url
        )
        
        logger.success(f"Bot is running with webhook: {self.settings.bot_webhook_url}")
        
        # Wait for shutdown signal
        await self._shutdown_event.wait()
        
        # Stop webhook
        await self.application.updater.stop()
        await self.application.stop()
    
    async def _handle_callback_query(self, update: Update, context) -> None:
        """Handle callback queries from inline keyboards."""
        from ..handlers.callbacks import handle_callback_query
        await handle_callback_query(update, context)
    
    async def _handle_message(self, update: Update, context) -> None:
        """Handle text messages."""
        from ..handlers.messages import handle_text_message
        await handle_text_message(update, context)
    
    async def _handle_photo(self, update: Update, context) -> None:
        """Handle photo messages."""
        from ..handlers.messages import handle_photo_message
        await handle_photo_message(update, context)
    
    async def _handle_document(self, update: Update, context) -> None:
        """Handle document messages."""
        from ..handlers.messages import handle_document_message
        await handle_document_message(update, context)
    
    async def _handle_inline_query(self, update: Update, context) -> None:
        """Handle inline queries."""
        from ..handlers.inline import handle_inline_query
        await handle_inline_query(update, context)
    
    async def _handle_new_member(self, update: Update, context) -> None:
        """Handle new member events."""
        from ..handlers.events import handle_new_member
        await handle_new_member(update, context)
    
    async def _handle_left_member(self, update: Update, context) -> None:
        """Handle left member events."""
        from ..handlers.events import handle_left_member
        await handle_left_member(update, context)
    
    def get_uptime(self) -> str:
        """Get bot uptime as formatted string."""
        if not self.start_time:
            return "Not started"
        
        uptime = datetime.now() - self.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check and return status."""
        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime": self.get_uptime(),
            "components": {}
        }
        
        # Check database
        try:
            db_healthy = await db_manager.health_check()
            health["components"]["database"] = "healthy" if db_healthy else "unhealthy"
        except Exception as e:
            health["components"]["database"] = f"error: {e}"
        
        # Check Redis
        if self.redis:
            try:
                await self.redis.ping()
                health["components"]["redis"] = "healthy"
            except Exception as e:
                health["components"]["redis"] = f"error: {e}"
        else:
            health["components"]["redis"] = "not configured"
        
        # Check AI services
        try:
            ai_health = await self.ai_orchestrator.health_check()
            health["components"]["ai_services"] = ai_health
        except Exception as e:
            health["components"]["ai_services"] = f"error: {e}"
        
        # Overall status
        unhealthy_components = [
            k for k, v in health["components"].items() 
            if isinstance(v, str) and ("error" in v or v == "unhealthy")
        ]
        
        if unhealthy_components:
            health["status"] = "degraded" if len(unhealthy_components) < len(health["components"]) else "unhealthy"
        
        return health