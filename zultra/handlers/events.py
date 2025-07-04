"""Event handlers for Zultra Telegram Bot."""

from telegram import Update
from telegram.ext import ContextTypes


async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle new member events."""
    # New member handling logic would go here
    pass


async def handle_left_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle left member events."""
    # Left member handling logic would go here
    pass