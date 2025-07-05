"""
Admin command handlers for Zultra Telegram Bot.
Handles moderation and administrative commands for group management.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.error import BadRequest, Forbidden
from loguru import logger

from ..core.config import get_settings
from ..db.database import get_session, create_or_update_user


class AdminHandlers:
    """Admin command handlers for moderation and management."""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Moderation actions tracking
        self.moderation_actions = {}
        
        # Lock types for group restrictions
        self.lock_types = {
            'messages': 'can_send_messages',
            'media': 'can_send_media_messages',
            'polls': 'can_send_polls',
            'stickers': 'can_send_other_messages',
            'links': 'can_add_web_page_previews',
            'forwards': 'can_send_messages',
            'all': 'all_permissions'
        }
    
    async def ban_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /ban command to ban users from the group."""
        try:
            user = update.effective_user
            chat = update.effective_chat
            
            # Check if command is used in a group
            if chat.type == 'private':
                await update.message.reply_text(
                    "❌ This command can only be used in groups."
                )
                return
            
            # Check if user is admin
            if not await self._is_admin(context.bot, chat.id, user.id):
                await update.message.reply_text(
                    "❌ Only administrators can use this command."
                )
                return
            
            # Check if bot has ban permissions
            bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
            if not bot_member.can_restrict_members:
                await update.message.reply_text(
                    "❌ I need 'Restrict Members' permission to ban users."
                )
                return
            
            # Get target user
            target_user = None
            reason = "No reason provided"
            
            if update.message.reply_to_message:
                target_user = update.message.reply_to_message.from_user
                if context.args:
                    reason = ' '.join(context.args)
            elif context.args:
                # Try to parse username or ID
                target_arg = context.args[0]
                if target_arg.startswith('@'):
                    target_arg = target_arg[1:]
                
                try:
                    if target_arg.isdigit():
                        target_user_id = int(target_arg)
                        target_member = await context.bot.get_chat_member(chat.id, target_user_id)
                        target_user = target_member.user
                    else:
                        # This would require a database lookup in a real implementation
                        await update.message.reply_text(
                            "❌ User not found. Reply to a message or use user ID."
                        )
                        return
                except:
                    await update.message.reply_text(
                        "❌ User not found or not in this group."
                    )
                    return
                
                if len(context.args) > 1:
                    reason = ' '.join(context.args[1:])
            
            if not target_user:
                await update.message.reply_text(
                    "🚫 <b>Ban User</b>\n\n"
                    "<b>Usage:</b>\n"
                    "• Reply to a message: /ban [reason]\n"
                    "• Use user ID: /ban [user_id] [reason]\n\n"
                    "<b>Examples:</b>\n"
                    "• /ban Spamming\n"
                    "• /ban 123456789 Inappropriate behavior\n\n"
                    "<i>Only admins can use this command</i>",
                    parse_mode=ParseMode.HTML
                )
                return
            
            # Check if target is admin
            if await self._is_admin(context.bot, chat.id, target_user.id):
                await update.message.reply_text(
                    "❌ Cannot ban administrators."
                )
                return
            
            # Check if target is bot owner
            if target_user.id in self.settings.get_owner_ids():
                await update.message.reply_text(
                    "❌ Cannot ban bot owner."
                )
                return
            
            try:
                # Ban the user
                await context.bot.ban_chat_member(chat.id, target_user.id)
                
                ban_text = f"""
🚫 <b>User Banned</b>

<b>👤 Banned User:</b> {target_user.first_name} (@{target_user.username or 'None'})
<b>🆔 User ID:</b> <code>{target_user.id}</code>
<b>👮 Banned by:</b> {user.first_name}
<b>📝 Reason:</b> {reason}
<b>⏰ Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>User has been permanently banned from the group.</i>
"""
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔓 Unban", callback_data=f"unban_{target_user.id}"),
                        InlineKeyboardButton("📊 User Info", callback_data=f"user_info_{target_user.id}")
                    ],
                    [
                        InlineKeyboardButton("📝 Add Note", callback_data=f"add_note_{target_user.id}"),
                        InlineKeyboardButton("📋 Ban History", callback_data="ban_history")
                    ]
                ])
                
                await update.message.reply_text(
                    ban_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard
                )
                
                # Log the action
                await self._log_moderation_action(
                    'ban', user.id, target_user.id, chat.id, reason
                )
                
                logger.info(f"User {target_user.id} banned by {user.id} in chat {chat.id}")
                
            except BadRequest as e:
                await update.message.reply_text(
                    f"❌ Failed to ban user: {str(e)}"
                )
            except Exception as e:
                logger.error(f"Error banning user: {e}")
                await update.message.reply_text(
                    "❌ An error occurred while banning the user."
                )
        
        except Exception as e:
            logger.error(f"Error in ban command: {e}")
            await update.message.reply_text("❌ Error processing ban command.")
    
    async def kick_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /kick command to remove users from the group."""
        try:
            user = update.effective_user
            chat = update.effective_chat
            
            # Check if command is used in a group
            if chat.type == 'private':
                await update.message.reply_text(
                    "❌ This command can only be used in groups."
                )
                return
            
            # Check if user is admin
            if not await self._is_admin(context.bot, chat.id, user.id):
                await update.message.reply_text(
                    "❌ Only administrators can use this command."
                )
                return
            
            # Get target user (similar logic to ban command)
            target_user = None
            reason = "No reason provided"
            
            if update.message.reply_to_message:
                target_user = update.message.reply_to_message.from_user
                if context.args:
                    reason = ' '.join(context.args)
            elif context.args:
                await update.message.reply_text(
                    "❌ Please reply to a message to kick a user."
                )
                return
            
            if not target_user:
                await update.message.reply_text(
                    "👢 <b>Kick User</b>\n\n"
                    "<b>Usage:</b> Reply to a message and use /kick [reason]\n\n"
                    "<b>Example:</b> /kick Temporary removal\n\n"
                    "<i>User can rejoin after being kicked</i>",
                    parse_mode=ParseMode.HTML
                )
                return
            
            # Check if target is admin
            if await self._is_admin(context.bot, chat.id, target_user.id):
                await update.message.reply_text(
                    "❌ Cannot kick administrators."
                )
                return
            
            try:
                # Kick the user (ban then unban)
                await context.bot.ban_chat_member(chat.id, target_user.id)
                await context.bot.unban_chat_member(chat.id, target_user.id)
                
                kick_text = f"""
👢 <b>User Kicked</b>

<b>👤 Kicked User:</b> {target_user.first_name} (@{target_user.username or 'None'})
<b>👮 Kicked by:</b> {user.first_name}
<b>📝 Reason:</b> {reason}
<b>⏰ Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>User can rejoin the group using an invite link.</i>
"""
                
                await update.message.reply_text(
                    kick_text,
                    parse_mode=ParseMode.HTML
                )
                
                # Log the action
                await self._log_moderation_action(
                    'kick', user.id, target_user.id, chat.id, reason
                )
                
                logger.info(f"User {target_user.id} kicked by {user.id} in chat {chat.id}")
                
            except Exception as e:
                logger.error(f"Error kicking user: {e}")
                await update.message.reply_text(
                    "❌ Failed to kick user. Check my permissions."
                )
        
        except Exception as e:
            logger.error(f"Error in kick command: {e}")
            await update.message.reply_text("❌ Error processing kick command.")
    
    async def mute_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /mute command to restrict user permissions."""
        try:
            user = update.effective_user
            chat = update.effective_chat
            
            if chat.type == 'private':
                await update.message.reply_text(
                    "❌ This command can only be used in groups."
                )
                return
            
            if not await self._is_admin(context.bot, chat.id, user.id):
                await update.message.reply_text(
                    "❌ Only administrators can use this command."
                )
                return
            
            # Get target user and duration
            target_user = None
            duration = None
            reason = "No reason provided"
            
            if update.message.reply_to_message:
                target_user = update.message.reply_to_message.from_user
                
                if context.args:
                    # Parse duration and reason
                    args = context.args
                    if args[0].endswith(('m', 'h', 'd')):
                        duration_str = args[0]
                        duration = self._parse_duration(duration_str)
                        if len(args) > 1:
                            reason = ' '.join(args[1:])
                    else:
                        reason = ' '.join(args)
            
            if not target_user:
                await update.message.reply_text(
                    "🔇 <b>Mute User</b>\n\n"
                    "<b>Usage:</b> Reply to a message and use:\n"
                    "• /mute [duration] [reason]\n"
                    "• /mute [reason]\n\n"
                    "<b>Duration examples:</b>\n"
                    "• 30m - 30 minutes\n"
                    "• 2h - 2 hours\n"
                    "• 1d - 1 day\n\n"
                    "<b>Example:</b> /mute 1h Spamming messages",
                    parse_mode=ParseMode.HTML
                )
                return
            
            if await self._is_admin(context.bot, chat.id, target_user.id):
                await update.message.reply_text(
                    "❌ Cannot mute administrators."
                )
                return
            
            try:
                # Calculate until_date if duration is specified
                until_date = None
                if duration:
                    until_date = datetime.now() + duration
                
                # Mute the user
                await context.bot.restrict_chat_member(
                    chat.id,
                    target_user.id,
                    permissions=self._get_muted_permissions(),
                    until_date=until_date
                )
                
                duration_text = f" for {self._format_duration(duration)}" if duration else " indefinitely"
                
                mute_text = f"""
🔇 <b>User Muted</b>

<b>👤 Muted User:</b> {target_user.first_name} (@{target_user.username or 'None'})
<b>👮 Muted by:</b> {user.first_name}
<b>⏱️ Duration:</b> {duration_text}
<b>📝 Reason:</b> {reason}
<b>⏰ Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>User cannot send messages{duration_text}.</i>
"""
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔊 Unmute", callback_data=f"unmute_{target_user.id}"),
                        InlineKeyboardButton("⏱️ Extend", callback_data=f"extend_mute_{target_user.id}")
                    ]
                ])
                
                await update.message.reply_text(
                    mute_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard
                )
                
                # Log the action
                await self._log_moderation_action(
                    'mute', user.id, target_user.id, chat.id, reason, duration
                )
                
                logger.info(f"User {target_user.id} muted by {user.id} in chat {chat.id}")
                
            except Exception as e:
                logger.error(f"Error muting user: {e}")
                await update.message.reply_text(
                    "❌ Failed to mute user. Check my permissions."
                )
        
        except Exception as e:
            logger.error(f"Error in mute command: {e}")
            await update.message.reply_text("❌ Error processing mute command.")
    
    async def warn_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /warn command to warn users."""
        try:
            user = update.effective_user
            chat = update.effective_chat
            
            if chat.type == 'private':
                await update.message.reply_text(
                    "❌ This command can only be used in groups."
                )
                return
            
            if not await self._is_admin(context.bot, chat.id, user.id):
                await update.message.reply_text(
                    "❌ Only administrators can use this command."
                )
                return
            
            target_user = None
            reason = "No reason provided"
            
            if update.message.reply_to_message:
                target_user = update.message.reply_to_message.from_user
                if context.args:
                    reason = ' '.join(context.args)
            
            if not target_user:
                await update.message.reply_text(
                    "⚠️ <b>Warn User</b>\n\n"
                    "<b>Usage:</b> Reply to a message and use /warn [reason]\n\n"
                    "<b>Example:</b> /warn Please follow group rules\n\n"
                    "<i>Users are automatically banned after 3 warnings</i>",
                    parse_mode=ParseMode.HTML
                )
                return
            
            if await self._is_admin(context.bot, chat.id, target_user.id):
                await update.message.reply_text(
                    "❌ Cannot warn administrators."
                )
                return
            
            # Get current warning count
            warning_count = await self._get_warning_count(target_user.id, chat.id)
            warning_count += 1
            
            # Save warning to database
            await self._add_warning(target_user.id, chat.id, user.id, reason)
            
            warn_text = f"""
⚠️ <b>User Warning #{warning_count}</b>

<b>👤 Warned User:</b> {target_user.first_name} (@{target_user.username or 'None'})
<b>👮 Warned by:</b> {user.first_name}
<b>📝 Reason:</b> {reason}
<b>📊 Total Warnings:</b> {warning_count}/3

"""
            
            if warning_count >= 3:
                # Auto-ban after 3 warnings
                try:
                    await context.bot.ban_chat_member(chat.id, target_user.id)
                    warn_text += "<b>🚫 Action:</b> User automatically banned for reaching 3 warnings!"
                    
                    await self._log_moderation_action(
                        'auto_ban', user.id, target_user.id, chat.id, "3 warnings reached"
                    )
                    
                except Exception as e:
                    warn_text += "<b>❌ Failed to auto-ban user.</b>"
            else:
                warn_text += f"<i>User will be banned after {3 - warning_count} more warning(s).</i>"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📋 Warning History", callback_data=f"warnings_{target_user.id}"),
                    InlineKeyboardButton("🗑️ Remove Warning", callback_data=f"remove_warn_{target_user.id}")
                ]
            ])
            
            await update.message.reply_text(
                warn_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
            logger.info(f"User {target_user.id} warned by {user.id} in chat {chat.id}")
            
        except Exception as e:
            logger.error(f"Error in warn command: {e}")
            await update.message.reply_text("❌ Error processing warn command.")
    
    async def purge_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /purge command to delete multiple messages."""
        try:
            user = update.effective_user
            chat = update.effective_chat
            
            if chat.type == 'private':
                await update.message.reply_text(
                    "❌ This command can only be used in groups."
                )
                return
            
            if not await self._is_admin(context.bot, chat.id, user.id):
                await update.message.reply_text(
                    "❌ Only administrators can use this command."
                )
                return
            
            # Check bot permissions
            bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
            if not bot_member.can_delete_messages:
                await update.message.reply_text(
                    "❌ I need 'Delete Messages' permission to purge messages."
                )
                return
            
            # Get number of messages to delete
            count = 1
            if context.args:
                try:
                    count = int(context.args[0])
                    if count < 1 or count > 100:
                        await update.message.reply_text(
                            "❌ Please specify a number between 1 and 100."
                        )
                        return
                except ValueError:
                    await update.message.reply_text(
                        "❌ Please specify a valid number."
                    )
                    return
            
            # If replying to a message, delete from that message to current
            start_message_id = update.message.message_id
            if update.message.reply_to_message:
                start_message_id = update.message.reply_to_message.message_id
            
            # Show confirmation
            confirm_text = f"""
🗑️ <b>Purge Confirmation</b>

<b>📊 Messages to delete:</b> {count}
<b>👮 Requested by:</b> {user.first_name}
<b>⏰ Time:</b> {datetime.now().strftime('%H:%M:%S')}

<b>⚠️ This action cannot be undone!</b>

<i>Click confirm to proceed with deletion.</i>
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Confirm Delete", callback_data=f"confirm_purge_{count}_{start_message_id}"),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel_purge")
                ]
            ])
            
            await update.message.reply_text(
                confirm_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in purge command: {e}")
            await update.message.reply_text("❌ Error processing purge command.")
    
    async def lock_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /lock command to restrict chat features."""
        try:
            user = update.effective_user
            chat = update.effective_chat
            
            if chat.type == 'private':
                await update.message.reply_text(
                    "❌ This command can only be used in groups."
                )
                return
            
            if not await self._is_admin(context.bot, chat.id, user.id):
                await update.message.reply_text(
                    "❌ Only administrators can use this command."
                )
                return
            
            if not context.args:
                await update.message.reply_text(
                    "🔒 <b>Lock Chat Features</b>\n\n"
                    "<b>Usage:</b> /lock [type]\n\n"
                    "<b>Available lock types:</b>\n"
                    "• <code>messages</code> - All messages\n"
                    "• <code>media</code> - Photos, videos, documents\n"
                    "• <code>stickers</code> - Stickers and GIFs\n"
                    "• <code>polls</code> - Polls and quizzes\n"
                    "• <code>links</code> - Web page previews\n"
                    "• <code>forwards</code> - Forwarded messages\n"
                    "• <code>all</code> - Everything\n\n"
                    "<b>Example:</b> /lock media",
                    parse_mode=ParseMode.HTML
                )
                return
            
            lock_type = context.args[0].lower()
            if lock_type not in self.lock_types:
                await update.message.reply_text(
                    f"❌ Unknown lock type: {lock_type}\n"
                    "Use /lock to see available types."
                )
                return
            
            try:
                # Apply the lock
                permissions = await self._get_current_permissions(context.bot, chat.id)
                if lock_type == 'all':
                    permissions = self._get_locked_permissions()
                else:
                    setattr(permissions, self.lock_types[lock_type], False)
                
                await context.bot.set_chat_permissions(chat.id, permissions)
                
                lock_text = f"""
🔒 <b>Chat Locked</b>

<b>🔐 Lock Type:</b> {lock_type.title()}
<b>👮 Locked by:</b> {user.first_name}
<b>⏰ Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>Only administrators can {lock_type} now.</i>
"""
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔓 Unlock", callback_data=f"unlock_{lock_type}"),
                        InlineKeyboardButton("📊 Lock Status", callback_data="lock_status")
                    ]
                ])
                
                await update.message.reply_text(
                    lock_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard
                )
                
                logger.info(f"Chat {chat.id} locked ({lock_type}) by {user.id}")
                
            except Exception as e:
                logger.error(f"Error locking chat: {e}")
                await update.message.reply_text(
                    "❌ Failed to lock chat. Check my permissions."
                )
        
        except Exception as e:
            logger.error(f"Error in lock command: {e}")
            await update.message.reply_text("❌ Error processing lock command.")
    
    async def unlock_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /unlock command to remove chat restrictions."""
        try:
            user = update.effective_user
            chat = update.effective_chat
            
            if chat.type == 'private':
                await update.message.reply_text(
                    "❌ This command can only be used in groups."
                )
                return
            
            if not await self._is_admin(context.bot, chat.id, user.id):
                await update.message.reply_text(
                    "❌ Only administrators can use this command."
                )
                return
            
            if not context.args:
                await update.message.reply_text(
                    "🔓 <b>Unlock Chat Features</b>\n\n"
                    "<b>Usage:</b> /unlock [type]\n\n"
                    "Use the same types as /lock command.\n"
                    "<b>Example:</b> /unlock media"
                )
                return
            
            unlock_type = context.args[0].lower()
            if unlock_type not in self.lock_types:
                await update.message.reply_text(
                    f"❌ Unknown unlock type: {unlock_type}"
                )
                return
            
            try:
                # Remove the lock
                permissions = await self._get_current_permissions(context.bot, chat.id)
                if unlock_type == 'all':
                    permissions = self._get_default_permissions()
                else:
                    setattr(permissions, self.lock_types[unlock_type], True)
                
                await context.bot.set_chat_permissions(chat.id, permissions)
                
                unlock_text = f"""
🔓 <b>Chat Unlocked</b>

<b>🔐 Unlock Type:</b> {unlock_type.title()}
<b>👮 Unlocked by:</b> {user.first_name}
<b>⏰ Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>Members can {unlock_type} again.</i>
"""
                
                await update.message.reply_text(
                    unlock_text,
                    parse_mode=ParseMode.HTML
                )
                
                logger.info(f"Chat {chat.id} unlocked ({unlock_type}) by {user.id}")
                
            except Exception as e:
                logger.error(f"Error unlocking chat: {e}")
                await update.message.reply_text(
                    "❌ Failed to unlock chat. Check my permissions."
                )
        
        except Exception as e:
            logger.error(f"Error in unlock command: {e}")
            await update.message.reply_text("❌ Error processing unlock command.")
    
    # Helper methods
    
    async def _is_admin(self, bot, chat_id: int, user_id: int) -> bool:
        """Check if user is admin in the chat."""
        try:
            member = await bot.get_chat_member(chat_id, user_id)
            return member.status in [ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR]
        except:
            return False
    
    async def _log_moderation_action(self, action: str, admin_id: int, target_id: int, 
                                   chat_id: int, reason: str, duration: timedelta = None):
        """Log moderation action to database."""
        try:
            async with get_session() as session:
                # In a real implementation, you'd save to a moderation_logs table
                pass
        except Exception as e:
            logger.error(f"Error logging moderation action: {e}")
    
    def _parse_duration(self, duration_str: str) -> timedelta:
        """Parse duration string to timedelta."""
        try:
            if duration_str.endswith('m'):
                return timedelta(minutes=int(duration_str[:-1]))
            elif duration_str.endswith('h'):
                return timedelta(hours=int(duration_str[:-1]))
            elif duration_str.endswith('d'):
                return timedelta(days=int(duration_str[:-1]))
            else:
                return timedelta(hours=1)  # Default 1 hour
        except:
            return timedelta(hours=1)
    
    def _format_duration(self, duration: timedelta) -> str:
        """Format timedelta to readable string."""
        if not duration:
            return "indefinitely"
        
        days = duration.days
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        
        return " ".join(parts) if parts else "less than a minute"
    
    def _get_muted_permissions(self):
        """Get permissions for muted users."""
        from telegram import ChatPermissions
        return ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False
        )
    
    def _get_locked_permissions(self):
        """Get permissions for fully locked chat."""
        from telegram import ChatPermissions
        return ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False
        )
    
    def _get_default_permissions(self):
        """Get default chat permissions."""
        from telegram import ChatPermissions
        return ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=False,
            can_invite_users=True,
            can_pin_messages=False
        )
    
    async def _get_current_permissions(self, bot, chat_id: int):
        """Get current chat permissions."""
        try:
            chat = await bot.get_chat(chat_id)
            return chat.permissions
        except:
            return self._get_default_permissions()
    
    async def _get_warning_count(self, user_id: int, chat_id: int) -> int:
        """Get warning count for user in chat."""
        try:
            async with get_session() as session:
                # In a real implementation, you'd query warnings table
                return 0
        except:
            return 0
    
    async def _add_warning(self, user_id: int, chat_id: int, admin_id: int, reason: str):
        """Add warning to database."""
        try:
            async with get_session() as session:
                # In a real implementation, you'd insert into warnings table
                pass
        except Exception as e:
            logger.error(f"Error adding warning: {e}")