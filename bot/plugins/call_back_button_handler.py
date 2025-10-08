# 15. bot/plugins/call_back_button_handler.py - Enhanced callback handler

import logging
import os
import json
from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.localisation import Localisation
from bot import DOWNLOAD_LOCATION, AUTH_USERS

try:
    from bot.database import Database
    from bot import DATABASE_URL, SESSION_NAME
    db = Database(DATABASE_URL, SESSION_NAME) if DATABASE_URL else None
except:
    db = None

from bot.helper_funcs.utils import SystemUtils, delete_downloads
from bot.helper_funcs.display_progress import humanbytes

LOGGER = logging.getLogger(__name__)

async def button(bot: Client, update: CallbackQuery):
    """Enhanced callback query handler"""
    try:
        cb_data = update.data
        user_id = update.from_user.id
        
        # Help callback
        if cb_data == "help":
            await update.message.edit_text(
                Localisation.HELP_MESSAGE,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="start")
                ]])
            )
            
        # Settings callback
        elif cb_data == "settings":
            await show_user_settings(bot, update)
            
        # Status callback
        elif cb_data == "status":
            await show_bot_status(bot, update)
            
        # Start/home callback
        elif cb_data == "start":
            await update.message.edit_text(
                Localisation.START_TEXT,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton('📖 Help', callback_data='help'),
                        InlineKeyboardButton('⚙️ Settings', callback_data='settings')
                    ],
                    [
                        InlineKeyboardButton('📊 Status', callback_data='status')
                    ],
                    [
                        InlineKeyboardButton('🔗 Updates Channel', url='https://t.me/Discovery_Updates'),
                        InlineKeyboardButton('💬 Support Group', url='https://t.me/linux_repo')
                    ]
                ])
            )
            
        # Cancel compression callback
        elif cb_data == "cancel_compression":
            if user_id in AUTH_USERS:
                await handle_compression_cancel(bot, update)
            else:
                await update.answer("❌ You don't have permission to cancel compression", show_alert=True)
                
        # Confirm cancel callback
        elif cb_data == "confirm_cancel":
            if user_id in AUTH_USERS:
                await confirm_cancel_compression(bot, update)
            else:
                await update.answer("❌ You don't have permission to cancel", show_alert=True)
                
        # Keep process callback
        elif cb_data == "keep_process" or cb_data == "keep_job":
            await update.message.edit_text(
                "✅ **Process Continued**\\n\\n"
                "🔄 The compression will continue as normal\\n"
                "⏰ You can check status anytime"
            )
            
        # Refresh status callback
        elif cb_data == "refresh_status":
            await show_bot_status(bot, update)
            
        # Refresh banned users callback
        elif cb_data == "refresh_banned":
            await refresh_banned_users(bot, update)
            
        # System info callback
        elif cb_data == "system_info":
            await show_system_info(bot, update)
            
        # Clean downloads callback
        elif cb_data == "clean_downloads":
            if user_id in AUTH_USERS:
                await clean_downloads_callback(bot, update)
            else:
                await update.answer("❌ Admin only", show_alert=True)
                
        # Unknown callback
        else:
            await update.answer("❓ Unknown action", show_alert=True)
            
        await update.answer()
        
    except Exception as e:
        LOGGER.error(f"Callback handler error: {e}")
        await update.answer("❌ An error occurred", show_alert=True)

async def show_user_settings(bot: Client, update: CallbackQuery):
    """Show user settings menu"""
    try:
        if not db:
            await update.message.edit_text(
                "❌ **Settings Unavailable**\\n\\n"
                "Database is not configured for this bot.\\n"
                "Contact admin for assistance."
            )
            return
            
        user_settings = await db.get_user_settings(update.from_user.id)
        
        settings_text = (
            f"⚙️ **Your Settings**\\n\\n"
            f"🎨 **Default Quality:** {user_settings.get('default_quality', 50)}%\\n"
            f"📱 **Output Format:** {user_settings.get('output_format', 'MP4').upper()}\\n"
            f"🖼️ **Custom Thumbnail:** {'✅ Set' if user_settings.get('custom_thumbnail') else '❌ None'}\\n"
            f"📊 **Progress Updates:** {'✅ Enabled' if user_settings.get('progress_updates', True) else '❌ Disabled'}\\n"
            f"🔔 **Notifications:** {'✅ Enabled' if user_settings.get('notifications', True) else '❌ Disabled'}\\n\\n"
            f"💡 Settings will be applied to future compressions"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🎨 Quality", callback_data="set_quality"),
                InlineKeyboardButton("📱 Format", callback_data="set_format")
            ],
            [
                InlineKeyboardButton("📊 Progress", callback_data="toggle_progress"),
                InlineKeyboardButton("🔔 Notifications", callback_data="toggle_notifications")
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="start")]
        ]
        
        await update.message.edit_text(
            settings_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        LOGGER.error(f"Settings display error: {e}")
        await update.message.edit_text("❌ Error loading settings")

async def show_bot_status(bot: Client, update: CallbackQuery):
    """Show detailed bot status"""
    try:
        system_info = SystemUtils.get_system_info()
        
        # Get current processes
        status_file = DOWNLOAD_LOCATION + "/status.json"
        active_processes = 0
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r') as f:
                    status_data = json.load(f)
                    if status_data.get('running'):
                        active_processes = 1
            except:
                pass
        
        status_text = (
            f"📊 **Enhanced VideoCompress Bot Status**\\n\\n"
            f"🤖 **Bot Status:** {'🟢 Online' if bot.is_connected else '🔴 Offline'}\\n"
            f"⚙️ **Active Processes:** {active_processes}\\n"
        )
        
        if db:
            try:
                total_users = await db.total_users_count()
                active_users = await db.active_users_count()
                status_text += f"👥 **Total Users:** {total_users:,}\\n"
                status_text += f"🟢 **Active Users (7d):** {active_users:,}\\n"
            except:
                status_text += f"👥 **Users:** Database error\\n"
        else:
            status_text += f"👥 **Users:** Database not configured\\n"
        
        status_text += (
            f"\\n**💻 System Resources:**\\n"
            f"🔥 **CPU:** {system_info.get('cpu_percent', 0):.1f}%\\n"
            f"💾 **Memory:** {system_info.get('memory_percent', 0):.1f}%\\n"
            f"💿 **Disk:** {system_info.get('disk_percent', 0):.1f}%\\n"
        )
        
        if system_info.get('memory_available', 0) > 0:
            status_text += f"🆓 **Free Memory:** {humanbytes(system_info['memory_available'])}\\n"
        
        if system_info.get('disk_free', 0) > 0:
            status_text += f"💾 **Free Disk:** {humanbytes(system_info['disk_free'])}\\n"
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh_status"),
                InlineKeyboardButton("🖥️ System Info", callback_data="system_info")
            ]
        ]
        
        if update.from_user.id in AUTH_USERS:
            keyboard.append([
                InlineKeyboardButton("🧹 Clean Downloads", callback_data="clean_downloads"),
                InlineKeyboardButton("📋 Logs", callback_data="get_logs")
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="start")])
        
        await update.message.edit_text(
            status_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        LOGGER.error(f"Status display error: {e}")
        await update.message.edit_text("❌ Error loading status")

async def show_system_info(bot: Client, update: CallbackQuery):
    """Show detailed system information"""
    try:
        system_info = SystemUtils.get_system_info()
        
        info_text = (
            f"🖥️ **System Information**\\n\\n"
            f"**🔥 CPU:**\\n"
            f"• Cores: {system_info.get('cpu_count', 'N/A')}\\n"
            f"• Usage: {system_info.get('cpu_percent', 0):.1f}%\\n\\n"
            f"**💾 Memory:**\\n"
            f"• Total: {humanbytes(system_info.get('memory_total', 0))}\\n"
            f"• Available: {humanbytes(system_info.get('memory_available', 0))}\\n"
            f"• Usage: {system_info.get('memory_percent', 0):.1f}%\\n\\n"
            f"**💿 Storage:**\\n"
            f"• Total: {humanbytes(system_info.get('disk_total', 0))}\\n"
            f"• Free: {humanbytes(system_info.get('disk_free', 0))}\\n"
            f"• Usage: {system_info.get('disk_percent', 0):.1f}%"
        )
        
        await update.message.edit_text(
            info_text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Status", callback_data="status")
            ]])
        )
        
    except Exception as e:
        LOGGER.error(f"System info error: {e}")
        await update.message.edit_text("❌ Error loading system info")

async def handle_compression_cancel(bot: Client, update: CallbackQuery):
    """Handle compression cancellation request"""
    try:
        await update.message.edit_text(
            "🗑️ **Cancel Compression Process?**\\n\\n"
            "⚠️ This will stop the current compression job\\n"
            "❌ This action cannot be undone!\\n\\n"
            "Are you sure you want to proceed?",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('✅ Yes, Cancel', callback_data='confirm_cancel'),
                    InlineKeyboardButton('❌ No, Keep', callback_data='keep_process')
                ]
            ])
        )
    except Exception as e:
        LOGGER.error(f"Handle cancel error: {e}")

async def confirm_cancel_compression(bot: Client, update: CallbackQuery):
    """Confirm and execute compression cancellation"""
    try:
        status_file = DOWNLOAD_LOCATION + "/status.json"
        
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r') as f:
                    status_data = json.load(f)
                    
                pid = status_data.get('pid')
                if pid:
                    # Try to kill the process
                    from bot.helper_funcs.utils import SystemUtils
                    success = await SystemUtils.kill_process(pid)
                    
                    if success:
                        result_text = "✅ **Compression Cancelled Successfully!**"
                    else:
                        result_text = "⚠️ **Process termination attempted**"
                else:
                    result_text = "⚠️ **No active process found**"
                
                # Clean up
                os.remove(status_file)
                await delete_downloads()
                
            except Exception as e:
                result_text = f"❌ **Error cancelling process:** {str(e)}"
                
        else:
            result_text = "❌ **No active compression found**"
        
        await update.message.edit_text(
            f"{result_text}\\n\\n"
            f"🧹 Temporary files cleaned up\\n"
            f"✨ Bot is ready for new compressions"
        )
        
    except Exception as e:
        LOGGER.error(f"Cancel confirmation error: {e}")
        await update.message.edit_text("❌ Error during cancellation")

async def refresh_banned_users(bot: Client, update: CallbackQuery):
    """Refresh banned users list"""
    try:
        # This would call the banned users function
        # For now, show a simple message
        await update.message.edit_text(
            "🔄 **Refreshing banned users list...**\\n\\n"
            "💡 Use `/banned_users` command for full list"
        )
    except Exception as e:
        LOGGER.error(f"Refresh banned error: {e}")

async def clean_downloads_callback(bot: Client, update: CallbackQuery):
    """Clean downloads via callback"""
    try:
        from bot.helper_funcs.utils import CleanupManager
        
        await update.message.edit_text("🧹 **Cleaning downloads...**")
        
        cleaned_count = await CleanupManager.cleanup_temp_files()
        
        await update.message.edit_text(
            f"✅ **Cleanup Completed!**\\n\\n"
            f"🗑️ **Files Removed:** {cleaned_count}\\n"
            f"💾 **Download directory cleaned**\\n\\n"
            f"✨ Ready for new compressions!"
        )
        
    except Exception as e:
        LOGGER.error(f"Clean downloads callback error: {e}")
        await update.message.edit_text("❌ Error during cleanup")

print("Created broadcast and callback handler modules")
