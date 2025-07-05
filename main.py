#!/usr/bin/env python3
"""
Production-ready main entry point for Zultra Telegram Bot.
Handles initialization, error recovery, and graceful shutdown.
"""

import sys
import os
import asyncio
import signal
from pathlib import Path

# Ensure the project root is in the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger
from zultra.core.bot import ZultraBot
from zultra.core.config import initialize_config, get_health_status
from zultra.core.errors import setup_error_handling


async def main():
    """Main entry point with comprehensive error handling."""
    bot = None
    
    try:
        # Initialize configuration
        logger.info("🚀 Starting Zultra Bot v2.0...")
        
        if not initialize_config():
            logger.critical("❌ Configuration initialization failed")
            sys.exit(1)
        
        # Setup error handling
        setup_error_handling()
        
        # Initialize bot
        bot = ZultraBot()
        
        success = await bot.initialize()
        if not success:
            logger.critical("❌ Bot initialization failed")
            sys.exit(1)
        
        # Determine startup mode
        use_webhook = os.getenv('BOT_WEBHOOK_URL') is not None
        
        # Start the bot
        logger.success("✅ Bot initialized successfully")
        await bot.start(use_webhook=use_webhook)
        
    except KeyboardInterrupt:
        logger.info("⚠️ Received interrupt signal")
    except Exception as e:
        logger.exception(f"❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        if bot:
            await bot.shutdown()
        logger.info("👋 Zultra Bot stopped")


def run_bot():
    """Run the bot with proper event loop management."""
    try:
        # Use uvloop for better performance if available
        try:
            import uvloop
            uvloop.install()
            logger.info("🚀 Using uvloop for enhanced performance")
        except ImportError:
            logger.info("📦 uvloop not available, using standard asyncio")
        
        # Run the bot
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("⚠️ Bot stopped by user")
    except Exception as e:
        logger.exception(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_bot()