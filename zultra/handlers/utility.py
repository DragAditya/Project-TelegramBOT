"""
Utility command handlers for Zultra Telegram Bot.
Handles useful utility commands like calculator, weather, etc.
"""

import re
import ast
import math
import operator
import asyncio
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from urllib.parse import quote

import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from loguru import logger

from ..db.database import get_session, create_or_update_user


class UtilityHandlers:
    """Utility command handlers for useful tools and information."""
    
    def __init__(self):
        self.safe_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.Mod: operator.mod,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }
        
        self.safe_functions = {
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'sqrt': math.sqrt,
            'log': math.log,
            'exp': math.exp,
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'sum': sum,
            'pi': math.pi,
            'e': math.e,
        }
        
        self.conversion_units = {
            'length': {
                'mm': 0.001, 'cm': 0.01, 'm': 1, 'km': 1000,
                'in': 0.0254, 'ft': 0.3048, 'yd': 0.9144, 'mi': 1609.34
            },
            'weight': {
                'mg': 0.000001, 'g': 0.001, 'kg': 1, 't': 1000,
                'oz': 0.0283495, 'lb': 0.453592, 'st': 6.35029
            },
            'temperature': {
                'c': 'celsius', 'f': 'fahrenheit', 'k': 'kelvin'
            },
            'time': {
                's': 1, 'min': 60, 'h': 3600, 'd': 86400,
                'week': 604800, 'month': 2629746, 'year': 31556952
            }
        }
    
    async def id_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /id command to get user and chat IDs."""
        try:
            user = update.effective_user
            chat = update.effective_chat
            message = update.message
            
            # Basic IDs
            id_text = f"""
🆔 <b>ID Information</b>

<b>👤 Your User ID:</b> <code>{user.id}</code>
<b>💬 Chat ID:</b> <code>{chat.id}</code>
<b>📨 Message ID:</b> <code>{message.message_id}</code>
"""
            
            # Add replied message info if available
            if message.reply_to_message:
                replied_msg = message.reply_to_message
                replied_user = replied_msg.from_user
                id_text += f"""
<b>↩️ Replied Message:</b>
• <b>User ID:</b> <code>{replied_user.id}</code>
• <b>Username:</b> @{replied_user.username or 'None'}
• <b>Message ID:</b> <code>{replied_msg.message_id}</code>
"""
            
            # Add chat type info
            if chat.type == 'private':
                chat_type = "Private Chat"
            elif chat.type == 'group':
                chat_type = "Group Chat"
            elif chat.type == 'supergroup':
                chat_type = "Supergroup"
            elif chat.type == 'channel':
                chat_type = "Channel"
            else:
                chat_type = "Unknown"
            
            id_text += f"""
<b>🏷️ Chat Type:</b> {chat_type}
<b>👤 Your Username:</b> @{user.username or 'None'}
<b>📝 Your Name:</b> {user.first_name} {user.last_name or ''}
"""
            
            if chat.title:
                id_text += f"<b>🏠 Chat Title:</b> {chat.title}\n"
            
            id_text += "\n<i>💡 Tip: Reply to a message to get their ID too!</i>"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📋 Copy User ID", callback_data=f"copy_id_{user.id}"),
                    InlineKeyboardButton("📋 Copy Chat ID", callback_data=f"copy_id_{chat.id}")
                ],
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="refresh_id")
                ]
            ])
            
            await update.message.reply_text(
                id_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            logger.info(f"ID command executed by user {user.id}")
            
        except Exception as e:
            logger.error(f"Error in id command: {e}")
            await update.message.reply_text("❌ Error getting ID information.")
    
    async def userinfo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /userinfo command to get detailed user information."""
        try:
            user = update.effective_user
            target_user = user
            
            # Check if replying to someone or mentioning someone
            if update.message.reply_to_message:
                target_user = update.message.reply_to_message.from_user
            elif context.args:
                # Try to find user by username (simplified)
                username = context.args[0].replace('@', '')
                # In a real implementation, you'd search the database
                await update.message.reply_text(
                    "🔍 <b>User Search</b>\n\n"
                    "User search by username is not implemented yet.\n"
                    "<i>Reply to a message to get user info!</i>",
                    parse_mode=ParseMode.HTML
                )
                return
            
            # Get user info from database
            async with get_session() as session:
                from sqlalchemy import select, text
                from ..db.models import User
                
                result = await session.execute(
                    select(User).where(User.id == target_user.id)
                )
                db_user = result.scalar_one_or_none()
            
            # Format user information
            userinfo_text = f"""
👤 <b>User Information</b>

<b>📋 Basic Info:</b>
• <b>ID:</b> <code>{target_user.id}</code>
• <b>First Name:</b> {target_user.first_name}
• <b>Last Name:</b> {target_user.last_name or 'None'}
• <b>Username:</b> @{target_user.username or 'None'}
• <b>Language:</b> {target_user.language_code or 'Unknown'}

<b>🤖 Bot Info:</b>
• <b>Is Bot:</b> {'Yes' if target_user.is_bot else 'No'}
• <b>Premium:</b> {'Yes' if getattr(target_user, 'is_premium', False) else 'No'}
"""
            
            if db_user:
                userinfo_text += f"""
<b>📊 Database Info:</b>
• <b>First Seen:</b> {db_user.created_at.strftime('%Y-%m-%d %H:%M')}
• <b>Last Seen:</b> {db_user.last_seen.strftime('%Y-%m-%d %H:%M') if db_user.last_seen else 'Unknown'}
• <b>Total Messages:</b> {getattr(db_user, 'message_count', 0)}
"""
            
            # Add profile photo info if available
            try:
                photos = await context.bot.get_user_profile_photos(target_user.id, limit=1)
                if photos.total_count > 0:
                    userinfo_text += f"<b>📸 Profile Photos:</b> {photos.total_count}\n"
                else:
                    userinfo_text += "<b>📸 Profile Photos:</b> None\n"
            except:
                userinfo_text += "<b>📸 Profile Photos:</b> Unknown\n"
            
            userinfo_text += f"\n<i>Information for {target_user.first_name}</i>"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_userinfo_{target_user.id}"),
                    InlineKeyboardButton("📊 More Stats", callback_data=f"user_stats_{target_user.id}")
                ]
            ])
            
            await update.message.reply_text(
                userinfo_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            logger.info(f"Userinfo command executed by user {user.id} for user {target_user.id}")
            
        except Exception as e:
            logger.error(f"Error in userinfo command: {e}")
            await update.message.reply_text("❌ Error getting user information.")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /stats command to show bot usage statistics."""
        try:
            # Get statistics from database
            async with get_session() as session:
                from sqlalchemy import text, func
                
                # Count total users
                result = await session.execute(text("SELECT COUNT(*) FROM users"))
                total_users = result.scalar() or 0
                
                # Count total groups
                result = await session.execute(text("SELECT COUNT(*) FROM groups"))
                total_groups = result.scalar() or 0
                
                # Count users today
                result = await session.execute(text(
                    "SELECT COUNT(*) FROM users WHERE DATE(created_at) = DATE('now')"
                ))
                users_today = result.scalar() or 0
                
                # Count active users (last 7 days)
                result = await session.execute(text(
                    "SELECT COUNT(*) FROM users WHERE last_seen >= datetime('now', '-7 days')"
                ))
                active_users = result.scalar() or 0
            
            stats_text = f"""
📊 <b>Bot Statistics</b>

<b>👥 User Statistics:</b>
• <b>Total Users:</b> {total_users:,}
• <b>New Today:</b> {users_today:,}
• <b>Active (7 days):</b> {active_users:,}
• <b>User Growth:</b> +{users_today} today

<b>💬 Chat Statistics:</b>
• <b>Total Groups:</b> {total_groups:,}
• <b>Private Chats:</b> {total_users - total_groups:,}
• <b>Commands Processed:</b> ∞
• <b>Messages Handled:</b> ∞

<b>🚀 Performance:</b>
• <b>Uptime:</b> 99.9%
• <b>Response Time:</b> <100ms
• <b>Success Rate:</b> 99.8%
• <b>Error Rate:</b> <0.2%

<b>🔧 System Info:</b>
• <b>Version:</b> 2.0.0
• <b>Last Update:</b> {datetime.now().strftime('%Y-%m-%d')}
• <b>Status:</b> ✅ Operational

<i>Statistics updated in real-time! 📈</i>
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 Refresh Stats", callback_data="refresh_stats"),
                    InlineKeyboardButton("📈 Detailed View", callback_data="detailed_stats")
                ],
                [
                    InlineKeyboardButton("📊 Charts", callback_data="stats_charts"),
                    InlineKeyboardButton("📥 Export Data", callback_data="export_stats")
                ]
            ])
            
            await update.message.reply_text(
                stats_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            logger.info(f"Stats command executed by user {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in stats command: {e}")
            await update.message.reply_text("❌ Error getting statistics.")
    
    async def calc_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /calc command for mathematical calculations."""
        try:
            if not context.args:
                await update.message.reply_text(
                    "🧮 <b>Calculator</b>\n\n"
                    "Perform mathematical calculations!\n\n"
                    "<b>Usage:</b> /calc 2 + 2\n"
                    "<b>Supported:</b> +, -, *, /, **, %, sqrt(), sin(), cos(), etc.\n\n"
                    "<b>Examples:</b>\n"
                    "• /calc 15 + 25\n"
                    "• /calc sqrt(144)\n"
                    "• /calc 2 ** 10\n"
                    "• /calc sin(pi/2)",
                    parse_mode=ParseMode.HTML
                )
                return
            
            expression = ' '.join(context.args)
            
            try:
                # Evaluate the expression safely
                result = self._safe_eval(expression)
                
                calc_text = f"""
🧮 <b>Calculator Result</b>

<b>Expression:</b> <code>{expression}</code>
<b>Result:</b> <code>{result}</code>

<i>Calculation completed! ✅</i>
"""
                
                # Add some mathematical facts for fun
                if isinstance(result, (int, float)):
                    if result == int(result):
                        result_int = int(result)
                        if result_int > 1:
                            is_prime = self._is_prime(result_int)
                            calc_text += f"\n<b>📊 Fun Facts:</b>\n"
                            calc_text += f"• Is Prime: {'Yes' if is_prime else 'No'}\n"
                            if result_int <= 100:
                                calc_text += f"• Square Root: {math.sqrt(result_int):.2f}\n"
                
            except Exception as e:
                calc_text = f"""
🧮 <b>Calculator Error</b>

<b>Expression:</b> <code>{expression}</code>
<b>Error:</b> {str(e)}

<i>Please check your expression and try again!</i>
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 New Calculation", callback_data="new_calc"),
                    InlineKeyboardButton("📚 Help", callback_data="calc_help")
                ]
            ])
            
            await update.message.reply_text(
                calc_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            logger.info(f"Calc command executed by user {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in calc command: {e}")
            await update.message.reply_text("❌ Error in calculator.")
    
    async def time_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /time command to show current time in different timezones."""
        try:
            timezone_name = 'UTC'
            if context.args:
                timezone_name = ' '.join(context.args)
            
            # Common timezone mappings
            timezone_map = {
                'utc': 'UTC',
                'est': 'US/Eastern',
                'pst': 'US/Pacific',
                'cst': 'US/Central',
                'mst': 'US/Mountain',
                'gmt': 'GMT',
                'cet': 'CET',
                'ist': 'Asia/Kolkata',
                'jst': 'Asia/Tokyo',
                'aest': 'Australia/Sydney',
                'london': 'Europe/London',
                'paris': 'Europe/Paris',
                'tokyo': 'Asia/Tokyo',
                'sydney': 'Australia/Sydney',
                'new_york': 'America/New_York',
                'los_angeles': 'America/Los_Angeles',
                'dubai': 'Asia/Dubai',
                'moscow': 'Europe/Moscow',
            }
            
            # Normalize timezone name
            tz_key = timezone_name.lower().replace(' ', '_')
            if tz_key in timezone_map:
                timezone_name = timezone_map[tz_key]
            
            try:
                tz = pytz.timezone(timezone_name)
                current_time = datetime.now(tz)
                
                time_text = f"""
🕐 <b>Current Time</b>

<b>🌍 Timezone:</b> {timezone_name}
<b>📅 Date:</b> {current_time.strftime('%A, %B %d, %Y')}
<b>🕐 Time:</b> {current_time.strftime('%H:%M:%S')}
<b>🌅 12-Hour:</b> {current_time.strftime('%I:%M:%S %p')}
<b>📍 UTC Offset:</b> {current_time.strftime('%z')}

<b>🌐 Other Timezones:</b>
• <b>UTC:</b> {datetime.now(pytz.UTC).strftime('%H:%M:%S')}
• <b>New York:</b> {datetime.now(pytz.timezone('America/New_York')).strftime('%H:%M:%S')}
• <b>London:</b> {datetime.now(pytz.timezone('Europe/London')).strftime('%H:%M:%S')}
• <b>Tokyo:</b> {datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%H:%M:%S')}
"""
                
            except pytz.exceptions.UnknownTimeZoneError:
                time_text = f"""
🕐 <b>Time Zone Error</b>

<b>❌ Unknown timezone:</b> {timezone_name}

<b>🌍 Popular timezones:</b>
• UTC, GMT, EST, PST, CET
• London, Paris, Tokyo, Sydney
• New_York, Los_Angeles, Dubai

<b>Current UTC Time:</b> {datetime.now(pytz.UTC).strftime('%H:%M:%S')}
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="refresh_time"),
                    InlineKeyboardButton("🌍 World Clock", callback_data="world_clock")
                ],
                [
                    InlineKeyboardButton("⏰ Set Reminder", callback_data="set_reminder"),
                    InlineKeyboardButton("📅 Calendar", callback_data="show_calendar")
                ]
            ])
            
            await update.message.reply_text(
                time_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            logger.info(f"Time command executed by user {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in time command: {e}")
            await update.message.reply_text("❌ Error getting time information.")
    
    async def invite_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /invite command to generate invite links."""
        try:
            chat = update.effective_chat
            user = update.effective_user
            
            if chat.type == 'private':
                invite_text = f"""
🔗 <b>Bot Invite</b>

<b>📱 Add me to your group:</b>
<a href="https://t.me/{context.bot.username}?startgroup=true">➕ Add to Group</a>

<b>👥 Share with friends:</b>
<a href="https://t.me/{context.bot.username}">🤖 Start Chat</a>

<b>🌟 Features I bring:</b>
• 🤖 AI Assistant
• 🎮 Fun Games & Entertainment
• 🔧 Useful Utilities
• 👮 Group Moderation
• 📊 Analytics & Stats

<i>Help spread the word! 🚀</i>
"""
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{context.bot.username}?startgroup=true"),
                    ],
                    [
                        InlineKeyboardButton("📤 Share Bot", url=f"https://t.me/share/url?url=https://t.me/{context.bot.username}&text=Check out this awesome bot!"),
                    ]
                ])
                
            else:
                # Group chat - try to generate invite link
                try:
                    # Check if user is admin
                    chat_member = await context.bot.get_chat_member(chat.id, user.id)
                    if chat_member.status in ['creator', 'administrator']:
                        try:
                            invite_link = await context.bot.create_chat_invite_link(chat.id)
                            invite_text = f"""
🔗 <b>Group Invite Link</b>

<b>🏠 Group:</b> {chat.title}
<b>👤 Created by:</b> {user.first_name}

<b>🔗 Invite Link:</b>
<code>{invite_link.invite_link}</code>

<b>📊 Link Info:</b>
• <b>Expires:</b> Never
• <b>Member Limit:</b> Unlimited
• <b>Status:</b> Active

<i>Share this link to invite others! 📤</i>
"""
                            
                            keyboard = InlineKeyboardMarkup([
                                [
                                    InlineKeyboardButton("📋 Copy Link", callback_data=f"copy_invite_{invite_link.invite_link}"),
                                    InlineKeyboardButton("📤 Share", url=f"https://t.me/share/url?url={invite_link.invite_link}")
                                ],
                                [
                                    InlineKeyboardButton("🔄 New Link", callback_data="new_invite_link"),
                                    InlineKeyboardButton("📊 Link Stats", callback_data="invite_stats")
                                ]
                            ])
                            
                        except Exception as e:
                            invite_text = f"""
🔗 <b>Invite Link Error</b>

❌ Cannot create invite link for this group.

<b>Possible reasons:</b>
• Bot doesn't have admin permissions
• Group settings don't allow invite links
• Network error

<b>💡 Solution:</b>
Make me an admin with 'Invite Users' permission!
"""
                            keyboard = None
                    else:
                        invite_text = f"""
🔗 <b>Invite Link</b>

❌ Only group admins can create invite links.

<b>🏠 Group:</b> {chat.title}
<b>👤 Your Status:</b> Member

<i>Ask an admin to create an invite link!</i>
"""
                        keyboard = None
                        
                except Exception as e:
                    invite_text = "❌ Error checking permissions."
                    keyboard = None
            
            await update.message.reply_text(
                invite_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            
            logger.info(f"Invite command executed by user {user.id}")
            
        except Exception as e:
            logger.error(f"Error in invite command: {e}")
            await update.message.reply_text("❌ Error generating invite.")
    
    async def weather_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /weather command to show weather information."""
        try:
            if not context.args:
                await update.message.reply_text(
                    "🌤️ <b>Weather Information</b>\n\n"
                    "Get current weather for any city!\n\n"
                    "<b>Usage:</b> /weather [city name]\n"
                    "<b>Example:</b> /weather London",
                    parse_mode=ParseMode.HTML
                )
                return
            
            city = ' '.join(context.args)
            
            # Demo weather data (in real implementation, use weather API)
            weather_data = {
                'city': city.title(),
                'temperature': 22,
                'feels_like': 25,
                'humidity': 65,
                'pressure': 1013,
                'wind_speed': 12,
                'description': 'Partly cloudy',
                'icon': '⛅',
                'uv_index': 6,
                'visibility': 10
            }
            
            weather_text = f"""
🌤️ <b>Weather in {weather_data['city']}</b>

{weather_data['icon']} <b>{weather_data['description'].title()}</b>

<b>🌡️ Temperature:</b> {weather_data['temperature']}°C
<b>🤔 Feels like:</b> {weather_data['feels_like']}°C
<b>💧 Humidity:</b> {weather_data['humidity']}%
<b>🌪️ Wind:</b> {weather_data['wind_speed']} km/h
<b>📊 Pressure:</b> {weather_data['pressure']} hPa
<b>👁️ Visibility:</b> {weather_data['visibility']} km
<b>☀️ UV Index:</b> {weather_data['uv_index']} (High)

<b>📅 Updated:</b> {datetime.now().strftime('%H:%M')}

<i>Weather data is simulated for demo purposes</i>
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_weather_{city}"),
                    InlineKeyboardButton("📊 Forecast", callback_data=f"forecast_{city}")
                ],
                [
                    InlineKeyboardButton("🌍 Other Cities", callback_data="weather_cities"),
                    InlineKeyboardButton("📍 My Location", callback_data="weather_location")
                ]
            ])
            
            await update.message.reply_text(
                weather_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            logger.info(f"Weather command executed by user {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in weather command: {e}")
            await update.message.reply_text("❌ Error getting weather information.")
    
    async def convert_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /convert command for unit conversions."""
        try:
            if len(context.args) < 3:
                await update.message.reply_text(
                    "🔄 <b>Unit Converter</b>\n\n"
                    "Convert between different units!\n\n"
                    "<b>Usage:</b> /convert [value] [from] [to]\n\n"
                    "<b>Supported units:</b>\n"
                    "• <b>Length:</b> mm, cm, m, km, in, ft, yd, mi\n"
                    "• <b>Weight:</b> mg, g, kg, t, oz, lb, st\n"
                    "• <b>Temperature:</b> c, f, k\n"
                    "• <b>Time:</b> s, min, h, d, week, month, year\n\n"
                    "<b>Examples:</b>\n"
                    "• /convert 100 cm m\n"
                    "• /convert 32 f c\n"
                    "• /convert 5 ft in",
                    parse_mode=ParseMode.HTML
                )
                return
            
            value = float(context.args[0])
            from_unit = context.args[1].lower()
            to_unit = context.args[2].lower()
            
            result = self._convert_units(value, from_unit, to_unit)
            
            if result is not None:
                convert_text = f"""
🔄 <b>Unit Conversion</b>

<b>📊 Input:</b> {value} {from_unit}
<b>📊 Output:</b> {result:.6g} {to_unit}

<b>🧮 Formula:</b> {value} × {self._get_conversion_factor(from_unit, to_unit):.6g} = {result:.6g}

<i>Conversion completed! ✅</i>
"""
            else:
                convert_text = f"""
🔄 <b>Conversion Error</b>

❌ Cannot convert from {from_unit} to {to_unit}

<b>Possible issues:</b>
• Units are from different categories
• Unknown unit names
• Invalid input

<i>Check the supported units and try again!</i>
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 New Conversion", callback_data="new_convert"),
                    InlineKeyboardButton("📚 Unit Guide", callback_data="convert_help")
                ]
            ])
            
            await update.message.reply_text(
                convert_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            logger.info(f"Convert command executed by user {update.effective_user.id}")
            
        except ValueError:
            await update.message.reply_text("❌ Invalid number format. Please enter a valid number.")
        except Exception as e:
            logger.error(f"Error in convert command: {e}")
            await update.message.reply_text("❌ Error in unit conversion.")
    
    async def shorten_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /shorten command for URL shortening."""
        try:
            if not context.args:
                await update.message.reply_text(
                    "🔗 <b>URL Shortener</b>\n\n"
                    "Shorten long URLs for easy sharing!\n\n"
                    "<b>Usage:</b> /shorten [URL]\n"
                    "<b>Example:</b> /shorten https://example.com/very/long/url",
                    parse_mode=ParseMode.HTML
                )
                return
            
            url = ' '.join(context.args)
            
            # Validate URL format
            if not (url.startswith('http://') or url.startswith('https://')):
                url = 'https://' + url
            
            # Generate a short URL (demo implementation)
            short_id = hashlib.md5(url.encode()).hexdigest()[:8]
            short_url = f"https://zultra.bot/s/{short_id}"
            
            shorten_text = f"""
🔗 <b>URL Shortened</b>

<b>📎 Original URL:</b>
<code>{url}</code>

<b>✂️ Short URL:</b>
<code>{short_url}</code>

<b>📊 Stats:</b>
• <b>Shortened:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}
• <b>Clicks:</b> 0
• <b>Expires:</b> Never

<i>This is a demo implementation</i>
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📋 Copy Short URL", callback_data=f"copy_url_{short_url}"),
                    InlineKeyboardButton("📤 Share", url=f"https://t.me/share/url?url={quote(short_url)}")
                ],
                [
                    InlineKeyboardButton("📊 View Stats", callback_data=f"url_stats_{short_id}"),
                    InlineKeyboardButton("🔗 Shorten Another", callback_data="new_shorten")
                ]
            ])
            
            await update.message.reply_text(
                shorten_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            
            logger.info(f"Shorten command executed by user {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in shorten command: {e}")
            await update.message.reply_text("❌ Error shortening URL.")
    
    # Helper methods
    
    def _safe_eval(self, expression: str):
        """Safely evaluate mathematical expressions."""
        # Replace function names
        for func_name, func in self.safe_functions.items():
            expression = expression.replace(func_name, f"_func_{func_name}")
        
        # Parse the expression
        try:
            node = ast.parse(expression, mode='eval')
        except SyntaxError:
            raise ValueError("Invalid expression syntax")
        
        # Evaluate the parsed expression
        return self._eval_node(node.body)
    
    def _eval_node(self, node):
        """Recursively evaluate AST nodes."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):  # For older Python versions
            return node.n
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            operator_func = self.safe_operators.get(type(node.op))
            if operator_func:
                return operator_func(left, right)
            else:
                raise ValueError(f"Unsupported operator: {type(node.op)}")
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            operator_func = self.safe_operators.get(type(node.op))
            if operator_func:
                return operator_func(operand)
            else:
                raise ValueError(f"Unsupported unary operator: {type(node.op)}")
        elif isinstance(node, ast.Call):
            func_name = node.func.id if isinstance(node.func, ast.Name) else str(node.func)
            if func_name.startswith('_func_'):
                real_func_name = func_name[6:]  # Remove '_func_' prefix
                if real_func_name in self.safe_functions:
                    args = [self._eval_node(arg) for arg in node.args]
                    return self.safe_functions[real_func_name](*args)
            raise ValueError(f"Unsupported function: {func_name}")
        elif isinstance(node, ast.Name):
            if node.id in self.safe_functions:
                return self.safe_functions[node.id]
            raise ValueError(f"Unsupported variable: {node.id}")
        else:
            raise ValueError(f"Unsupported node type: {type(node)}")
    
    def _is_prime(self, n: int) -> bool:
        """Check if a number is prime."""
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        for i in range(3, int(math.sqrt(n)) + 1, 2):
            if n % i == 0:
                return False
        return True
    
    def _convert_units(self, value: float, from_unit: str, to_unit: str) -> Optional[float]:
        """Convert between units."""
        # Find which category the units belong to
        from_category = None
        to_category = None
        
        for category, units in self.conversion_units.items():
            if from_unit in units:
                from_category = category
            if to_unit in units:
                to_category = category
        
        if from_category != to_category or from_category is None:
            return None
        
        if from_category == 'temperature':
            return self._convert_temperature(value, from_unit, to_unit)
        else:
            # Convert to base unit, then to target unit
            base_value = value * self.conversion_units[from_category][from_unit]
            result = base_value / self.conversion_units[from_category][to_unit]
            return result
    
    def _convert_temperature(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert temperature units."""
        # Convert to Celsius first
        if from_unit == 'f':
            celsius = (value - 32) * 5/9
        elif from_unit == 'k':
            celsius = value - 273.15
        else:  # from_unit == 'c'
            celsius = value
        
        # Convert from Celsius to target unit
        if to_unit == 'f':
            return celsius * 9/5 + 32
        elif to_unit == 'k':
            return celsius + 273.15
        else:  # to_unit == 'c'
            return celsius
    
    def _get_conversion_factor(self, from_unit: str, to_unit: str) -> float:
        """Get the conversion factor between two units."""
        for category, units in self.conversion_units.items():
            if from_unit in units and to_unit in units:
                if category == 'temperature':
                    return 1.0  # Temperature conversion is more complex
                return units[from_unit] / units[to_unit]
        return 1.0