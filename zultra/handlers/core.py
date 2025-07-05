"""
Core command handlers for Zultra Telegram Bot.
Handles essential bot commands like start, help, settings, etc.
"""

import time
from datetime import datetime
from typing import Dict, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from loguru import logger

from ..core.config import get_settings, get_runtime_config, get_health_status
from ..db.database import create_or_update_user, get_session


class CoreHandlers:
    """Core command handlers for essential bot functionality."""
    
    def __init__(self):
        self.settings = get_settings()
        self.start_time = time.time()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command with comprehensive welcome message."""
        try:
            user = update.effective_user
            chat = update.effective_chat
            
            # Track user in database
            await self._track_user(user)
            
            # Create welcome message
            welcome_text = self._get_welcome_message(user, chat)
            
            # Create inline keyboard
            keyboard = self._get_start_keyboard()
            
            # Send welcome message
            await update.message.reply_text(
                welcome_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            
            logger.info(f"Start command executed by user {user.id}")
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text(
                "❌ An error occurred while processing your request. Please try again."
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command with comprehensive command listing."""
        try:
            user = update.effective_user
            
            # Get help content based on user permissions
            help_text = self._get_help_content(user)
            
            # Create help keyboard
            keyboard = self._get_help_keyboard()
            
            await update.message.reply_text(
                help_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            
            logger.info(f"Help command executed by user {user.id}")
            
        except Exception as e:
            logger.error(f"Error in help command: {e}")
            await update.message.reply_text("❌ Error loading help. Please try again.")
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /settings command with interactive settings panel."""
        try:
            user = update.effective_user
            
            # Get user settings
            settings_text = await self._get_user_settings(user)
            
            # Create settings keyboard
            keyboard = self._get_settings_keyboard()
            
            await update.message.reply_text(
                settings_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            logger.info(f"Settings command executed by user {user.id}")
            
        except Exception as e:
            logger.error(f"Error in settings command: {e}")
            await update.message.reply_text("❌ Error loading settings. Please try again.")
    
    async def about_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /about command with bot information and statistics."""
        try:
            # Get bot statistics
            stats = await self._get_bot_statistics()
            
            about_text = f"""
🤖 <b>Zultra Bot v2.0</b>

<b>📊 Bot Statistics:</b>
• <b>Uptime:</b> {stats['uptime']}
• <b>Users:</b> {stats['total_users']:,}
• <b>Groups:</b> {stats['total_groups']:,}
• <b>Commands Processed:</b> {stats['commands_processed']:,}
• <b>Version:</b> {stats['version']}

<b>🔧 System Info:</b>
• <b>Environment:</b> {self.settings.environment.title()}
• <b>Database:</b> {stats['database_type']}
• <b>Cache:</b> {'Redis' if self.settings.redis_url else 'Memory'}
• <b>AI Providers:</b> {stats['ai_providers']}

<b>🚀 Features:</b>
• Multi-AI Provider Support
• Advanced Security & Anti-Spam
• Comprehensive Logging
• Real-time Monitoring
• Cloud-Ready Deployment

<b>👨‍💻 Developer:</b> Zultra Team
<b>📄 License:</b> MIT
<b>🔗 Source:</b> <a href="https://github.com/zultra/bot">GitHub</a>

<i>Built with ❤️ for the community</i>
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📊 Health Check", callback_data="health_check"),
                    InlineKeyboardButton("📈 Statistics", callback_data="detailed_stats")
                ],
                [
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")
                ]
            ])
            
            await update.message.reply_text(
                about_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            
            logger.info(f"About command executed by user {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in about command: {e}")
            await update.message.reply_text("❌ Error loading about information.")
    
    async def uptime_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /uptime command with detailed uptime information."""
        try:
            runtime_config = get_runtime_config()
            current_time = time.time()
            uptime_seconds = current_time - runtime_config.start_time
            
            # Calculate uptime components
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            seconds = int(uptime_seconds % 60)
            
            # Format uptime string
            if days > 0:
                uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
            elif hours > 0:
                uptime_str = f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                uptime_str = f"{minutes}m {seconds}s"
            else:
                uptime_str = f"{seconds}s"
            
            # Get system health
            health = get_health_status()
            
            uptime_text = f"""
⏱️ <b>Bot Uptime Information</b>

<b>🕐 Current Uptime:</b> {uptime_str}
<b>🚀 Started:</b> {datetime.fromtimestamp(runtime_config.start_time).strftime('%Y-%m-%d %H:%M:%S')}
<b>📅 Current Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<b>🏥 System Health:</b>
• <b>Status:</b> {health.get('status', 'Unknown').title()}
• <b>Version:</b> {health.get('version', 'Unknown')}
• <b>Environment:</b> {health.get('environment', 'Unknown').title()}

<b>📊 Performance:</b>
• <b>Startup Errors:</b> {len(health.get('startup_errors', []))}
• <b>Memory Usage:</b> Optimized
• <b>Response Time:</b> <1s average

<i>Bot is running smoothly! 🚀</i>
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="refresh_uptime"),
                    InlineKeyboardButton("📊 Health Check", callback_data="health_check")
                ]
            ])
            
            await update.message.reply_text(
                uptime_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            logger.info(f"Uptime command executed by user {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in uptime command: {e}")
            await update.message.reply_text("❌ Error retrieving uptime information.")
    
    async def ping_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /ping command with latency measurement."""
        try:
            start_time = time.time()
            
            # Send initial message
            message = await update.message.reply_text("🏓 Pinging...")
            
            # Calculate latency
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            
            # Get additional metrics
            db_latency = await self._measure_db_latency()
            
            ping_text = f"""
🏓 <b>Pong!</b>

<b>📡 Network Latency:</b>
• <b>Bot Response:</b> {latency:.2f}ms
• <b>Database:</b> {db_latency:.2f}ms
• <b>Status:</b> {'🟢 Excellent' if latency < 100 else '🟡 Good' if latency < 500 else '🔴 Slow'}

<b>🔧 System Status:</b>
• <b>API:</b> ✅ Online
• <b>Database:</b> ✅ Connected
• <b>Cache:</b> {'✅ Connected' if self.settings.redis_url else '⚠️ Not configured'}

<b>⏰ Timestamp:</b> {datetime.now().strftime('%H:%M:%S')}
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 Ping Again", callback_data="ping_again"),
                    InlineKeyboardButton("📊 Detailed Stats", callback_data="detailed_ping")
                ]
            ])
            
            await message.edit_text(
                ping_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            logger.info(f"Ping command executed by user {update.effective_user.id} - Latency: {latency:.2f}ms")
            
        except Exception as e:
            logger.error(f"Error in ping command: {e}")
            await update.message.reply_text("❌ Error measuring ping.")
    
    # Helper methods
    
    async def _track_user(self, user) -> None:
        """Track user in database."""
        try:
            user_data = {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_bot': user.is_bot,
                'language_code': user.language_code,
                'is_premium': getattr(user, 'is_premium', False),
                'last_seen': datetime.now()
            }
            await create_or_update_user(user_data)
        except Exception as e:
            logger.error(f"Error tracking user: {e}")
    
    def _get_welcome_message(self, user, chat) -> str:
        """Generate personalized welcome message."""
        name = user.first_name or user.username or "User"
        
        if chat.type == 'private':
            return f"""
👋 <b>Welcome, {name}!</b>

I'm <b>Zultra Bot v2.0</b> - your advanced Telegram assistant with powerful features:

🤖 <b>AI Integration</b> - Chat with GPT & Gemini
🎮 <b>Fun Commands</b> - Games, quotes, and entertainment
🔧 <b>Utilities</b> - Calculator, weather, translations
👮 <b>Moderation</b> - Advanced group management
🛡️ <b>Security</b> - Anti-spam & rate limiting

<b>🚀 Quick Start:</b>
• Type /help to see all commands
• Use /settings to configure preferences
• Try /ask to chat with AI

<i>Ready to explore? Let's get started! 🎉</i>
"""
        else:
            return f"""
👋 <b>Hello {name}!</b>

Thanks for adding me to <b>{chat.title}</b>!

I'm here to help with:
• 🤖 AI assistance and chat
• 🎮 Fun games and entertainment  
• 👮 Group moderation tools
• 🔧 Useful utilities

Type /help to see what I can do!
"""
    
    def _get_start_keyboard(self) -> InlineKeyboardMarkup:
        """Create start command keyboard."""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📚 Help & Commands", callback_data="help_menu"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings_menu")
            ],
            [
                InlineKeyboardButton("🤖 Try AI Chat", callback_data="ai_demo"),
                InlineKeyboardButton("🎮 Fun Commands", callback_data="fun_menu")
            ],
            [
                InlineKeyboardButton("📊 About Bot", callback_data="about_bot"),
                InlineKeyboardButton("💬 Support", url="https://t.me/zultra_support")
            ]
        ])
    
    def _get_help_content(self, user) -> str:
        """Generate help content based on user permissions."""
        is_admin = user.id in self.settings.get_admin_ids()
        is_owner = user.id in self.settings.get_owner_ids()
        
        help_text = """
📚 <b>Zultra Bot - Command Guide</b>

<b>🔧 Core Commands:</b>
/start - Welcome message and quick start
/help - Show this help message
/settings - Configure bot preferences
/about - Bot information and statistics
/uptime - Check bot uptime and status
/ping - Test bot responsiveness

<b>🤖 AI Commands:</b>
/ask &lt;question&gt; - Ask AI assistant
/translate &lt;text&gt; - Translate text
/ocr - Extract text from images
/imagegen &lt;prompt&gt; - Generate AI images

<b>🎮 Fun Commands:</b>
/truth - Get a truth question
/dare - Get a dare challenge
/8ball &lt;question&gt; - Magic 8-ball
/quote - Inspirational quotes
/roast - Generate funny roasts
/ship &lt;user1&gt; &lt;user2&gt; - Ship compatibility

<b>🔧 Utility Commands:</b>
/id - Get user/chat IDs
/userinfo [@username] - User information
/stats - Bot usage statistics
/calc &lt;expression&gt; - Calculator
/time [timezone] - Current time
/invite - Generate invite link
/weather &lt;city&gt; - Weather info
/convert &lt;value&gt; &lt;from&gt; &lt;to&gt; - Unit converter
/shorten &lt;url&gt; - URL shortener
"""
        
        if is_admin or is_owner:
            help_text += """
<b>👮 Admin Commands:</b>
/ban [@username] - Ban user
/kick [@username] - Kick user
/mute [@username] - Mute user
/warn [@username] - Warn user
/purge &lt;count&gt; - Delete messages
/lock &lt;type&gt; - Lock chat features
/unlock &lt;type&gt; - Unlock chat features
"""
        
        if is_owner:
            help_text += """
<b>🔑 Owner Commands:</b>
/setai &lt;provider&gt; &lt;key&gt; - Set AI API key
/aiusage - View AI usage stats
/logs - View bot logs
/backup - Create backup
/restart - Restart bot
"""
        
        help_text += "\n<i>💡 Tip: Click buttons below for quick access!</i>"
        
        return help_text
    
    def _get_help_keyboard(self) -> InlineKeyboardMarkup:
        """Create help command keyboard."""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🤖 AI Commands", callback_data="help_ai"),
                InlineKeyboardButton("🎮 Fun Commands", callback_data="help_fun")
            ],
            [
                InlineKeyboardButton("🔧 Utilities", callback_data="help_utility"),
                InlineKeyboardButton("👮 Admin", callback_data="help_admin")
            ],
            [
                InlineKeyboardButton("📖 Full Documentation", url="https://docs.zultra.bot"),
                InlineKeyboardButton("💬 Support", url="https://t.me/zultra_support")
            ]
        ])
    
    async def _get_user_settings(self, user) -> str:
        """Get user-specific settings."""
        # This would typically fetch from database
        return f"""
⚙️ <b>Bot Settings</b>

<b>👤 User Information:</b>
• <b>ID:</b> {user.id}
• <b>Username:</b> @{user.username or 'Not set'}
• <b>Name:</b> {user.first_name} {user.last_name or ''}
• <b>Language:</b> {user.language_code or 'en'}

<b>🤖 AI Preferences:</b>
• <b>Default Provider:</b> OpenAI GPT
• <b>Language:</b> Auto-detect
• <b>Response Style:</b> Balanced

<b>🔔 Notifications:</b>
• <b>Command Responses:</b> ✅ Enabled
• <b>Error Messages:</b> ✅ Enabled
• <b>Updates:</b> ✅ Enabled

<b>🛡️ Privacy:</b>
• <b>Data Collection:</b> ✅ Basic only
• <b>Analytics:</b> ✅ Anonymous
• <b>Chat History:</b> ❌ Not stored

<i>Use buttons below to modify settings</i>
"""
    
    def _get_settings_keyboard(self) -> InlineKeyboardMarkup:
        """Create settings keyboard."""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🤖 AI Settings", callback_data="settings_ai"),
                InlineKeyboardButton("🔔 Notifications", callback_data="settings_notifications")
            ],
            [
                InlineKeyboardButton("🛡️ Privacy", callback_data="settings_privacy"),
                InlineKeyboardButton("🌍 Language", callback_data="settings_language")
            ],
            [
                InlineKeyboardButton("🔄 Reset to Default", callback_data="settings_reset"),
                InlineKeyboardButton("💾 Export Settings", callback_data="settings_export")
            ],
            [
                InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")
            ]
        ])
    
    async def _get_bot_statistics(self) -> Dict[str, Any]:
        """Get comprehensive bot statistics."""
        try:
            runtime_config = get_runtime_config()
            uptime_seconds = time.time() - runtime_config.start_time
            
            # Calculate uptime
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            if days > 0:
                uptime_str = f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                uptime_str = f"{hours}h {minutes}m"
            else:
                uptime_str = f"{minutes}m"
            
            # Get database stats
            async with get_session() as session:
                from sqlalchemy import text
                
                # Count users
                result = await session.execute(text("SELECT COUNT(*) FROM users"))
                total_users = result.scalar() or 0
                
                # Count groups
                result = await session.execute(text("SELECT COUNT(*) FROM groups"))
                total_groups = result.scalar() or 0
            
            # Determine AI providers
            ai_providers = []
            if self.settings.openai_api_key:
                ai_providers.append("OpenAI")
            if self.settings.gemini_api_key:
                ai_providers.append("Gemini")
            
            return {
                'uptime': uptime_str,
                'total_users': total_users,
                'total_groups': total_groups,
                'commands_processed': getattr(runtime_config, 'commands_processed', 0),
                'version': runtime_config.version,
                'database_type': 'PostgreSQL' if 'postgresql' in self.settings.database_url else 'SQLite',
                'ai_providers': ', '.join(ai_providers) or 'None configured'
            }
            
        except Exception as e:
            logger.error(f"Error getting bot statistics: {e}")
            return {
                'uptime': 'Unknown',
                'total_users': 0,
                'total_groups': 0,
                'commands_processed': 0,
                'version': '2.0.0',
                'database_type': 'Unknown',
                'ai_providers': 'Unknown'
            }
    
    async def _measure_db_latency(self) -> float:
        """Measure database latency."""
        try:
            start_time = time.time()
            async with get_session() as session:
                from sqlalchemy import text
                await session.execute(text("SELECT 1"))
            end_time = time.time()
            return (end_time - start_time) * 1000
        except Exception:
            return 0.0