"""
Main entry point for Zultra Telegram Bot.
Handles bot initialization and startup.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from zultra.core import setup_logging, ZultraBot


async def main():
    """Main function to start the bot."""
    try:
        # Setup logging first
        setup_logging()
        logger.info("Starting Zultra Telegram Bot...")
        
        # Create and initialize bot
        bot = ZultraBot()
        await bot.initialize()
        
        # Determine if we should use webhook based on environment
        use_webhook = os.getenv("USE_WEBHOOK", "false").lower() == "true"
        
        # Start the bot
        await bot.start(use_webhook=use_webhook)
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown complete")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)