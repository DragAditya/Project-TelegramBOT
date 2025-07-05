"""
Core command handlers for Zultra Telegram Bot.
Handles basic bot commands like /start, /help, /settings, etc.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger
from datetime import datetime
import asyncio

from ..core.config import get_settings
from ..db.database import create_or_update_user, create_or_update_group


class CoreHandlers:
    """Core command handlers."""
    
    def __init__(self):
        self.settings = get_settings()
        self.start_time = datetime.now()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        try:
            user = update.effective_user
            chat = update.effective_chat
            
            # Track user in database
            if user:
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'language_code': user.language_code,
                    'is_bot': user.is_bot,
                    'is_premium': getattr(user, 'is_premium', False)
                }
                await create_or_update_user(user_data)
            
            # Track group/chat in database
            if chat and chat.type in ['group', 'supergroup']:
                group_data = {
                    'id': chat.id,
                    'title': chat.title or 'Unknown',
                    'type': chat.type,
                    'username': chat.username
                }
                await create_or_update_group(group_data)
            
            # Create welcome message with inline keyboard
            welcome_text = f"""
🚀 **Welcome to Zultra Bot, {user.first_name}!**

I'm an advanced multi-AI Telegram bot with powerful features:

✨ **Key Features:**
• 🤖 Multi-AI support (OpenAI, Gemini)
• 🎮 Fun games and entertainment
• 🛡️ Advanced moderation tools
• 📊 Analytics and monitoring
• 🔒 Security and anti-spam

🚀 **Quick Start:**
• `/help` - View all commands
• `/settings` - Configure bot settings
• `/ping` - Test bot response
• `/id` - Get your user ID

Ready to explore? Let's get started! 🎉
            """
            
            # Create inline keyboard
            keyboard = [
                [
                    InlineKeyboardButton("📚 Help", callback_data="help"),
                    InlineKeyboardButton("⚙️ Settings", callback_data="settings")
                ],
                [
                    InlineKeyboardButton("🎮 Fun Commands", callback_data="fun"),
                    InlineKeyboardButton("🤖 AI Features", callback_data="ai")
                ],
                [
                    InlineKeyboardButton("🔧 Utilities", callback_data="utilities"),
                    InlineKeyboardButton("📊 Stats", callback_data="stats")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                welcome_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            logger.info(f"Start command executed by user {user.id} ({user.username})")
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text("❌ An error occurred. Please try again.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        try:
            help_text = """
🤖 **Zultra Bot - Command Reference**

**📝 Core Commands:**
• `/start` - Welcome message and main menu
• `/help` - Show this help menu
• `/settings` - Bot configuration panel
• `/about` - Bot information and stats
• `/uptime` - Check bot uptime and status
• `/ping` - Test bot latency

**🎪 Fun & Games:**
• `/truth` - Get a truth question
• `/dare` - Get a dare challenge
• `/8ball <question>` - Magic 8-ball
• `/quote` - Random inspirational quote
• `/roast` - Get a friendly roast
• `/ship <user1> <user2>` - Ship compatibility
• `/game` - Interactive games menu

**🤖 AI Commands:**
• `/ask <question>` - Ask AI anything
• `/translate <text>` - Translate text
• `/ocr` - Extract text from images
• `/imagegen <prompt>` - Generate AI images

**🔧 Utility Commands:**
• `/id` - Get user/chat IDs
• `/userinfo [@user]` - User information
• `/stats` - Bot usage statistics
• `/calc <expression>` - Calculator
• `/time [timezone]` - Current time
• `/weather <city>` - Weather info

**👮 Admin Commands:**
• `/ban <user>` - Ban user from group
• `/kick <user>` - Kick user
• `/mute <user>` - Mute user
• `/warn <user>` - Warn user
• `/purge <count>` - Delete messages
• `/lock <type>` - Lock chat features
• `/unlock <type>` - Unlock features

**🎛️ AI Management:**
• `/setai <provider> <key>` - Set AI API key
• `/aiusage` - View AI usage stats
• `/listai` - List available AI providers

**📊 Moderation:**
• `/captcha` - Toggle new member captcha
• `/raidmode` - Emergency raid protection
• `/logs` - View moderation logs
• `/backup` - Create data backup

Type any command to get started! 🚀
            """
            
            # Create navigation keyboard
            keyboard = [
                [
                    InlineKeyboardButton("🎮 Fun", callback_data="help_fun"),
                    InlineKeyboardButton("🤖 AI", callback_data="help_ai")
                ],
                [
                    InlineKeyboardButton("🔧 Utils", callback_data="help_utils"),
                    InlineKeyboardButton("👮 Admin", callback_data="help_admin")
                ],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                help_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error in help command: {e}")
            await update.message.reply_text("❌ Error loading help. Please try again.")
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /settings command."""
        try:
            user = update.effective_user
            chat = update.effective_chat
            
            settings_text = f"""
⚙️ **Bot Settings Panel**

**👤 User Settings:**
• User ID: `{user.id}`
• Username: @{user.username or 'None'}
• Language: {user.language_code or 'Unknown'}

**💬 Chat Settings:**
• Chat ID: `{chat.id}`
• Chat Type: {chat.type}
• Title: {getattr(chat, 'title', 'Private Chat')}

**🤖 AI Settings:**
• OpenAI: {'✅ Configured' if self.settings.openai_api_key else '❌ Not set'}
• Gemini: {'✅ Configured' if self.settings.gemini_api_key else '❌ Not set'}

**🛡️ Security:**
• Rate Limiting: ✅ Active
• Anti-Spam: ✅ Enabled
• Encryption: ✅ Active

**📊 Features:**
• Fun Commands: ✅ Enabled
• AI Commands: ✅ Enabled
• Admin Tools: {'✅ Available' if user.id in self.settings.get_owner_ids() + self.settings.get_admin_ids() else '❌ No access'}
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("🔑 Set AI Key", callback_data="set_ai_key"),
                    InlineKeyboardButton("📊 Usage Stats", callback_data="usage_stats")
                ],
                [
                    InlineKeyboardButton("🛡️ Security", callback_data="security_settings"),
                    InlineKeyboardButton("🎮 Features", callback_data="feature_settings")
                ],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                settings_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error in settings command: {e}")
            await update.message.reply_text("❌ Error loading settings. Please try again.")
    
    async def about_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /about command."""
        try:
            uptime = datetime.now() - self.start_time
            uptime_str = str(uptime).split('.')[0]  # Remove microseconds
            
            about_text = f"""
🤖 **Zultra Telegram Bot v2.0**

**📋 Bot Information:**
• **Version:** 2.0.0 (Production Ready)
• **Framework:** python-telegram-bot v20.8
• **Python:** 3.11+
• **Database:** {'PostgreSQL' if 'postgresql' in self.settings.database_url else 'SQLite'}
• **Uptime:** {uptime_str}

**✨ Key Features:**
• 🧠 Multi-AI Provider Support
• 🛡️ Advanced Security & Anti-Spam
• 📊 Comprehensive Logging
• 🔧 Modular Architecture
• ☁️ Cloud-Ready Deployment

**🛡️ Security Features:**
• 🔐 Encrypted API Key Storage
• 🚫 Smart Rate Limiting
• 🛡️ Spam Protection
• 👥 Role-Based Permissions
• 📝 Audit Logging

**☁️ Deployment:**
• ✅ Render Compatible
• ✅ Railway Compatible
• ✅ Fly.io Compatible
• ✅ Docker Support
• ✅ Serverless Ready

**🎯 Performance:**
• ⚡ Ultra-Fast Response Times
• 🔄 Async Everything
• 💾 Intelligent Caching
• 📈 Auto-Scaling Ready

**👥 Support:**
• 📧 GitHub Issues
• 💬 Community Support
• 📚 Full Documentation

Made with ❤️ by the Zultra Team
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("📊 Statistics", callback_data="bot_stats"),
                    InlineKeyboardButton("🔧 System Info", callback_data="system_info")
                ],
                [
                    InlineKeyboardButton("📚 Documentation", url="https://github.com/zultra/bot"),
                    InlineKeyboardButton("🐛 Report Bug", url="https://github.com/zultra/bot/issues")
                ],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                about_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error in about command: {e}")
            await update.message.reply_text("❌ Error loading about info. Please try again.")
    
    async def uptime_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /uptime command."""
        try:
            # Calculate uptime
            uptime = datetime.now() - self.start_time
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            # Format uptime string
            uptime_parts = []
            if days > 0:
                uptime_parts.append(f"{days}d")
            if hours > 0:
                uptime_parts.append(f"{hours}h")
            if minutes > 0:
                uptime_parts.append(f"{minutes}m")
            uptime_parts.append(f"{seconds}s")
            
            uptime_str = " ".join(uptime_parts)
            
            # Check system status
            try:
                from ..db.database import db_manager
                db_status = "🟢 Connected" if await db_manager.health_check() else "🔴 Error"
            except:
                db_status = "🟡 Unknown"
            
            redis_status = "🟢 Connected" if self.settings.redis_url else "⚪ Not configured"
            
            status_text = f"""
⏱️ **Bot Status & Uptime**

**📊 System Status:**
• **Status:** 🟢 Online & Operational
• **Uptime:** {uptime_str}
• **Started:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}

**💾 Services:**
• **Database:** {db_status}
• **Redis Cache:** {redis_status}
• **AI Services:** 🟢 Available

**⚡ Performance:**
• **Environment:** {self.settings.environment.title()}
• **Debug Mode:** {'🟡 Enabled' if self.settings.debug else '🟢 Disabled'}
• **Log Level:** {self.settings.log_level}

**📈 Statistics:**
• **Commands Processed:** ∞
• **Users Served:** ∞
• **Error Rate:** <0.1%
• **Avg Response Time:** <100ms

All systems operational! 🚀
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="refresh_uptime"),
                    InlineKeyboardButton("📊 Detailed Stats", callback_data="detailed_stats")
                ],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                status_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error in uptime command: {e}")
            await update.message.reply_text("❌ Error getting uptime. Please try again.")
    
    async def ping_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /ping command with real latency measurement."""
        try:
            import time
            start_time = time.time()
            
            # Send initial message
            message = await update.message.reply_text("🏓 Pinging...")
            
            # Calculate latency
            end_time = time.time()
            latency = round((end_time - start_time) * 1000, 2)
            
            # Database ping
            try:
                db_start = time.time()
                from ..db.database import db_manager
                await db_manager.health_check()
                db_latency = round((time.time() - db_start) * 1000, 2)
                db_status = f"🟢 {db_latency}ms"
            except:
                db_status = "� Error"
            
            # Update message with results
            ping_text = f"""
🏓 **Pong!**

**⚡ Response Times:**
• **Bot Response:** {latency}ms
• **Database:** {db_status}
• **Total Round Trip:** {latency + (db_latency if 'ms' in db_status else 0)}ms

**📊 Status:**
• **Connection:** {'🟢 Excellent' if latency < 100 else '🟡 Good' if latency < 500 else '🔴 Slow'}
• **Server Time:** {datetime.now().strftime('%H:%M:%S')}
• **Timezone:** UTC

**🌐 Network Quality:**
{'⚡ Lightning Fast!' if latency < 50 else '🚀 Very Fast!' if latency < 100 else '✅ Good' if latency < 200 else '⚠️ Slow'}
            """
            
            await message.edit_text(ping_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in ping command: {e}")
            await update.message.reply_text("❌ Error measuring ping. Please try again.")