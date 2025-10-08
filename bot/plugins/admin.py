# 13. bot/plugins/admin.py - Enhanced admin functions

import logging
import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

try:
    from bot.database import Database
    from bot import DATABASE_URL, SESSION_NAME
    db = Database(DATABASE_URL, SESSION_NAME) if DATABASE_URL else None
except:
    db = None

from bot import AUTH_USERS, LOG_FILE_ZZGEVC
from bot.helper_funcs.utils import SystemUtils
from bot.helper_funcs.display_progress import humanbytes
from datetime import datetime

LOGGER = logging.getLogger(__name__)

async def sts(bot: Client, update: Message):
    """Enhanced status command"""
    try:
        if not db:
            await update.reply_text("❌ Database not available for statistics")
            return
            
        total_users = await db.total_users_count()
        active_users = await db.active_users_count()
        system_info = SystemUtils.get_system_info()
        
        # Get uptime
        uptime = datetime.now() - datetime.fromtimestamp(bot.start_time if hasattr(bot, 'start_time') else 0)
        uptime_str = str(uptime).split('.')[0] if uptime.total_seconds() > 0 else "Just started"
        
        status_text = (
            f"📊 **Enhanced VideoCompress Bot Status**\\n\\n"
            f"👥 **Total Users:** {total_users:,}\\n"
            f"🟢 **Active Users (7d):** {active_users:,}\\n"
            f"⏰ **Uptime:** {uptime_str}\\n\\n"
            f"**💻 System Information:**\\n"
            f"🔥 **CPU Usage:** {system_info.get('cpu_percent', 0):.1f}%\\n"
            f"💾 **Memory Usage:** {system_info.get('memory_percent', 0):.1f}%\\n"
            f"💿 **Disk Usage:** {system_info.get('disk_percent', 0):.1f}%\\n"
        )
        
        if system_info.get('memory_total', 0) > 0:
            status_text += f"📊 **Total Memory:** {humanbytes(system_info['memory_total'])}\\n"
            status_text += f"🆓 **Available Memory:** {humanbytes(system_info['memory_available'])}\\n"
        
        if system_info.get('disk_total', 0) > 0:
            status_text += f"💽 **Total Disk:** {humanbytes(system_info['disk_total'])}\\n"
            status_text += f"💾 **Free Disk:** {humanbytes(system_info['disk_free'])}\\n"
        
        status_text += f"\\n🤖 **Enhanced VideoCompress Bot v2.0**\\n"
        status_text += f"📅 **Current Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        await update.reply_text(
            status_text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh_status")
            ]])
        )
        
    except Exception as e:
        LOGGER.error(f"Status command error: {e}")
        await update.reply_text("❌ Error getting status")

async def ban(bot: Client, update: Message):
    """Enhanced ban user command"""
    try:
        if not db:
            await update.reply_text("❌ Database not available")
            return
            
        if len(update.command) < 2:
            await update.reply_text(
                "**Usage:** `/ban <user_id> [duration] [reason]`\\n\\n"
                "**Examples:**\\n"
                "• `/ban 123456789` - Permanent ban\\n"
                "• `/ban 123456789 3600` - Ban for 1 hour\\n"
                "• `/ban 123456789 3600 Spamming` - Ban with reason"
            )
            return
            
        try:
            user_id = int(update.command[1])
        except ValueError:
            await update.reply_text("❌ Invalid user ID")
            return
            
        duration = int(update.command[2]) if len(update.command) > 2 and update.command[2].isdigit() else 0
        reason = " ".join(update.command[3:]) if len(update.command) > 3 else "No reason provided"
        
        # Check if user exists
        if not await db.is_user_exist(user_id):
            await update.reply_text("❌ User not found in database")
            return
        
        success = await db.ban_user(user_id, duration, reason, update.from_user.id)
        
        if success:
            duration_text = f"{duration} seconds" if duration > 0 else "permanent"
            await update.reply_text(
                f"✅ **User Banned Successfully!**\\n\\n"
                f"👤 **User ID:** {user_id}\\n"
                f"⏰ **Duration:** {duration_text}\\n"
                f"📝 **Reason:** {reason}\\n"
                f"👮 **Banned by:** {update.from_user.first_name} ({update.from_user.id})"
            )
            
            # Try to notify the user
            try:
                ban_message = (
                    f"🚫 **You have been banned from Enhanced VideoCompress Bot**\\n\\n"
                    f"⏰ **Duration:** {duration_text}\\n"
                    f"📝 **Reason:** {reason}\\n\\n"
                    f"📞 Contact support if you think this is a mistake."
                )
                await bot.send_message(user_id, ban_message)
            except:
                pass  # User might have blocked the bot
            
        else:
            await update.reply_text("❌ Failed to ban user")
            
    except Exception as e:
        LOGGER.error(f"Ban command error: {e}")
        await update.reply_text("❌ Error in ban command")

async def unban(bot: Client, update: Message):
    """Enhanced unban user command"""
    try:
        if not db:
            await update.reply_text("❌ Database not available")
            return
            
        if len(update.command) < 2:
            await update.reply_text(
                "**Usage:** `/unban <user_id>`\\n\\n"
                "**Example:** `/unban 123456789`"
            )
            return
            
        try:
            user_id = int(update.command[1])
        except ValueError:
            await update.reply_text("❌ Invalid user ID")
            return
            
        # Check if user exists
        if not await db.is_user_exist(user_id):
            await update.reply_text("❌ User not found in database")
            return
        
        # Check if user is actually banned
        ban_status = await db.get_ban_status(user_id)
        if not ban_status.get('is_banned', False):
            await update.reply_text("❌ User is not banned")
            return
        
        success = await db.remove_ban(user_id)
        
        if success:
            await update.reply_text(
                f"✅ **User Unbanned Successfully!**\\n\\n"
                f"👤 **User ID:** {user_id}\\n"
                f"👮 **Unbanned by:** {update.from_user.first_name} ({update.from_user.id})"
            )
            
            # Try to notify the user
            try:
                unban_message = (
                    f"✅ **You have been unbanned from Enhanced VideoCompress Bot**\\n\\n"
                    f"🎉 You can now use the bot again!\\n"
                    f"💡 Please follow the bot rules to avoid future bans."
                )
                await bot.send_message(user_id, unban_message)
            except:
                pass  # User might have blocked the bot
            
        else:
            await update.reply_text("❌ Failed to unban user")
            
    except Exception as e:
        LOGGER.error(f"Unban command error: {e}")
        await update.reply_text("❌ Error in unban command")

async def _banned_usrs(bot: Client, update: Message):
    """Show banned users with pagination"""
    try:
        if not db:
            await update.reply_text("❌ Database not available")
            return
            
        banned_users = await db.get_all_banned_users()
        
        if not banned_users:
            await update.reply_text(
                "✅ **No Banned Users**\\n\\n"
                "🎉 All users are currently allowed to use the bot!"
            )
            return
        
        # Paginate results
        page_size = 10
        total_pages = (len(banned_users) + page_size - 1) // page_size
        
        text = f"🚫 **Banned Users** (Total: {len(banned_users)})\\n\\n"
        
        for i, user in enumerate(banned_users[:page_size]):
            ban_status = user.get('ban_status', {})
            reason = ban_status.get('ban_reason', 'No reason')[:30]  # Limit reason length
            banned_on = ban_status.get('banned_on', 'Unknown')
            
            text += f"{i+1}. **{user['id']}** - {reason}\\n"
            text += f"   📅 Banned: {banned_on[:10]}\\n\\n"
        
        keyboard = []
        if total_pages > 1:
            keyboard.append([
                InlineKeyboardButton("◀️ Prev", callback_data="banned_page_0"),
                InlineKeyboardButton(f"1/{total_pages}", callback_data="banned_info"),
                InlineKeyboardButton("Next ▶️", callback_data="banned_page_1")
            ])
        
        keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data="refresh_banned")])
        
        await update.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        LOGGER.error(f"Banned users command error: {e}")
        await update.reply_text("❌ Error getting banned users")

async def get_logs(bot: Client, update: Message):
    """Send log file with options"""
    try:
        if not os.path.exists(LOG_FILE_ZZGEVC):
            await update.reply_text("❌ Log file not found")
            return
        
        # Get file size
        file_size = os.path.getsize(LOG_FILE_ZZGEVC)
        
        if file_size > 50 * 1024 * 1024:  # 50MB limit
            await update.reply_text(
                f"⚠️ **Log file is too large to send**\\n\\n"
                f"📏 **Size:** {humanbytes(file_size)}\\n"
                f"💡 **Solution:** Use `/logs tail` to get recent logs only"
            )
            return
        
        # Check if user wants tail logs
        if len(update.command) > 1 and update.command[1].lower() == 'tail':
            # Get last 1000 lines
            try:
                import subprocess
                result = subprocess.run(
                    ['tail', '-n', '1000', LOG_FILE_ZZGEVC],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    # Create temporary file with tail logs
                    temp_log = LOG_FILE_ZZGEVC + '.tail'
                    with open(temp_log, 'w') as f:
                        f.write(result.stdout)
                    
                    await bot.send_document(
                        chat_id=update.chat.id,
                        document=temp_log,
                        caption="📋 **Recent Bot Logs (Last 1000 lines)**"
                    )
                    
                    # Clean up temp file
                    os.remove(temp_log)
                else:
                    raise Exception("tail command failed")
            except:
                # Fallback: read last part of file
                with open(LOG_FILE_ZZGEVC, 'r') as f:
                    lines = f.readlines()
                    recent_lines = lines[-1000:] if len(lines) > 1000 else lines
                
                temp_log = LOG_FILE_ZZGEVC + '.tail'
                with open(temp_log, 'w') as f:
                    f.writelines(recent_lines)
                
                await bot.send_document(
                    chat_id=update.chat.id,
                    document=temp_log,
                    caption="📋 **Recent Bot Logs**"
                )
                
                os.remove(temp_log)
        else:
            # Send full log file
            await bot.send_document(
                chat_id=update.chat.id,
                document=LOG_FILE_ZZGEVC,
                caption=f"📋 **Complete Bot Logs**\\n📏 **Size:** {humanbytes(file_size)}"
            )
        
    except Exception as e:
        LOGGER.error(f"Logs command error: {e}")
        await update.reply_text("❌ Error sending logs")

async def restart_bot(bot: Client, update: Message):
    """Restart bot (admin only)"""
    try:
        await update.reply_text(
            "🔄 **Restarting Enhanced VideoCompress Bot...**\\n\\n"
            "⏰ This may take a few moments\\n"
            "✨ All processes will be stopped safely"
        )
        
        # Clean up any ongoing processes
        from bot.helper_funcs.utils import delete_downloads
        await delete_downloads()
        
        # Send restart signal
        import os
        import signal
        os.kill(os.getpid(), signal.SIGTERM)
        
    except Exception as e:
        LOGGER.error(f"Restart command error: {e}")
        await update.reply_text("❌ Error restarting bot")

async def clear_downloads(bot: Client, update: Message):
    """Clear download directory (admin only)"""
    try:
        from bot.helper_funcs.utils import CleanupManager
        
        cleaned_count = await CleanupManager.cleanup_temp_files()
        
        await update.reply_text(
            f"🧹 **Cleanup Completed!**\\n\\n"
            f"🗑️ **Files Removed:** {cleaned_count}\\n"
            f"💾 **Space Freed:** Calculating...\\n\\n"
            f"✨ Download directory cleaned successfully!"
        )
        
    except Exception as e:
        LOGGER.error(f"Clear downloads error: {e}")
        await update.reply_text("❌ Error clearing downloads")

# Add handlers for new admin commands
async def sys_info(bot: Client, update: Message):
    """Detailed system information"""
    try:
        system_info = SystemUtils.get_system_info()
        
        info_text = (
            f"🖥️ **Detailed System Information**\\n\\n"
            f"**🔥 CPU Information:**\\n"
            f"• Cores: {system_info.get('cpu_count', 'N/A')}\\n"
            f"• Usage: {system_info.get('cpu_percent', 0):.1f}%\\n\\n"
            f"**💾 Memory Information:**\\n"
            f"• Total: {humanbytes(system_info.get('memory_total', 0))}\\n"
            f"• Available: {humanbytes(system_info.get('memory_available', 0))}\\n"
            f"• Used: {system_info.get('memory_percent', 0):.1f}%\\n\\n"
            f"**💿 Disk Information:**\\n"
            f"• Total: {humanbytes(system_info.get('disk_total', 0))}\\n"
            f"• Free: {humanbytes(system_info.get('disk_free', 0))}\\n"
            f"• Used: {system_info.get('disk_percent', 0):.1f}%\\n\\n"
            f"🤖 **Enhanced VideoCompress Bot v2.0**"
        )
        
        await update.reply_text(info_text)
        
    except Exception as e:
        LOGGER.error(f"System info error: {e}")
        await update.reply_text("❌ Error getting system information")

print("Created enhanced admin module")
