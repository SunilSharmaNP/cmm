# 12. bot/plugins/incoming_message_fn.py - Enhanced message handler

import datetime
import logging
import os
import time
import asyncio
import json
from typing import Optional

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, UsernameNotOccupied

try:
    from bot.database import Database  
except ImportError:
    Database = None
    
from bot.localisation import Localisation
from bot import (
    DOWNLOAD_LOCATION,
    AUTH_USERS,
    LOG_CHANNEL,
    UPDATES_CHANNEL,
    DATABASE_URL,
    SESSION_NAME,
    ALLOWED_FILE_TYPES,
    TG_MAX_FILE_SIZE
)

from bot.helper_funcs.ffmpeg import (
    convert_video,
    media_info,
    take_screen_shot
)

from bot.helper_funcs.display_progress import (
    progress_for_pyrogram,
    TimeFormatter,
    humanbytes
)

from bot.helper_funcs.utils import (
    delete_downloads,
    ValidationUtils
)

LOGGER = logging.getLogger(__name__)

# Initialize database if available
db = None
if Database and DATABASE_URL:
    try:
        db = Database(DATABASE_URL, SESSION_NAME)
    except Exception as e:
        LOGGER.error(f"Database initialization failed: {e}")

# Track current processes
CURRENT_PROCESSES = {}
CHAT_FLOOD = {}

async def incoming_start_message_f(bot: Client, update: Message):
    """Enhanced /start command handler"""
    try:
        # Add user to database if available
        if db and not await db.is_user_exist(update.from_user.id):
            await db.add_user(
                update.from_user.id, 
                update.from_user.username,
                update.from_user.first_name
            )
        
        # Update last activity
        if db:
            await db.update_user_activity(update.from_user.id)
        
        # Check force subscription
        if UPDATES_CHANNEL and not await check_subscription(bot, update):
            return
        
        # Send enhanced start message
        await bot.send_message(
            chat_id=update.chat.id,
            text=Localisation.START_TEXT,
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
            ]),
            reply_to_message_id=update.id
        )
        
    except Exception as e:
        LOGGER.error(f"Error in start handler: {e}")
        await update.reply_text("❌ An error occurred. Please try again later.")

async def incoming_compress_message_f(bot: Client, update: Message):
    """Enhanced /compress command handler"""
    try:
        # Add user if not exists
        if db and not await db.is_user_exist(update.from_user.id):
            await db.add_user(
                update.from_user.id,
                update.from_user.username, 
                update.from_user.first_name
            )
        
        # Update activity
        if db:
            await db.update_user_activity(update.from_user.id)
        
        # Check subscription
        if UPDATES_CHANNEL and not await check_subscription(bot, update):
            return
        
        # Check if reply to media
        if not update.reply_to_message or not update.reply_to_message.video:
            await update.reply_text(
                Localisation.ERROR_MESSAGES['no_reply'],
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton('📖 How to Use', callback_data='help')
                ]])
            )
            return
        
        # Parse compression settings
        target_percentage = 50
        isAuto = False
        
        if len(update.command) > 1:
            try:
                arg = update.command[1]
                if arg.lower() in ['high', 'medium', 'low']:
                    quality_map = {'high': 25, 'medium': 50, 'low': 75}
                    target_percentage = quality_map[arg.lower()]
                elif arg.isdigit() and 10 <= int(arg) <= 90:
                    target_percentage = int(arg)
                else:
                    await update.reply_text(Localisation.ERROR_MESSAGES['invalid_quality'])
                    return
            except:
                await update.reply_text(Localisation.ERROR_MESSAGES['invalid_quality'])
                return
        else:
            isAuto = True

        # Validate file
        video = update.reply_to_message.video
        if not await validate_video_file(video, update):
            return
        
        # Check if user has active process
        if update.from_user.id in CURRENT_PROCESSES:
            await update.reply_text(
                "⚠️ You already have a compression in progress!\\n"
                "⏰ Please wait for it to complete."
            )
            return

        user_file = str(update.from_user.id) + ".FFMpegRoBot.mkv"
        saved_file_path = DOWNLOAD_LOCATION + "/" + user_file
        
        LOGGER.info(f"Starting compression for user {update.from_user.id}")
        
        d_start = time.time()
        c_start = time.time()
        u_start = time.time()
        
        status = DOWNLOAD_LOCATION + "/status.json"
        
        if not os.path.exists(status):
            # Mark user as having active process
            CURRENT_PROCESSES[update.from_user.id] = True
            
            sent_message = await bot.send_message(
                chat_id=update.chat.id,
                text=Localisation.DOWNLOAD_START,
                reply_to_message_id=update.id
            )
            
            # Send log to channel if configured
            if LOG_CHANNEL:
                try:
                    utc_now = datetime.datetime.utcnow()
                    ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
                    ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
                    
                    download_start = await bot.send_message(
                        LOG_CHANNEL, 
                        f"🔥 **Bot Busy Now!** \\n\\n"
                        f"👤 **User:** {update.from_user.first_name} ({update.from_user.id})\\n"
                        f"📁 **File:** {video.file_name or 'Unknown'}\\n"
                        f"📏 **Size:** {humanbytes(video.file_size)}\\n"
                        f"🎯 **Quality:** {target_percentage}%\\n"
                        f"⏰ **Started:** `{ist}` (GMT+05:30)",
                        parse_mode="markdown"
                    )
                except Exception as e:
                    LOGGER.warning(f"Could not send log message: {e}")
                    download_start = None
            else:
                download_start = None

            try:
                # Download file
                d_start = time.time()
                
                status_data = {
                    'running': True,
                    'message': sent_message.id,
                    'user_id': update.from_user.id
                }
                
                with open(status, 'w') as f:
                    json.dump(status_data, f, indent=2)

                video_download = await bot.download_media(
                    message=update.reply_to_message,
                    file_name=saved_file_path,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        bot,
                        Localisation.DOWNLOAD_START,
                        sent_message,
                        d_start
                    )
                )

                LOGGER.info(f"Download completed: {video_download}")

                if video_download is None:
                    await cleanup_process(update.from_user.id, sent_message, download_start, "Download cancelled")
                    return

                await sent_message.edit_text(Localisation.SAVED_RECVD_DOC_FILE)

            except Exception as e:
                LOGGER.error(f"Download error: {e}")
                await cleanup_process(update.from_user.id, sent_message, download_start, f"Download failed: {e}")
                return

        else:
            # Process already running
            await update.reply_text(Localisation.FF_MPEG_RO_BOT_STOR_AGE_ALREADY_EXISTS)
            return

        if os.path.exists(saved_file_path):
            downloaded_time = TimeFormatter((time.time() - d_start) * 1000)
            
            # Get media info
            duration, bitrate = await media_info(saved_file_path)
            
            if duration is None or bitrate is None:
                await cleanup_process(
                    update.from_user.id, sent_message, download_start, 
                    "Failed to get video metadata"
                )
                return

            # Generate thumbnail
            thumb_image_path = await take_screen_shot(
                saved_file_path,
                os.path.dirname(os.path.abspath(saved_file_path)),
                (duration / 2)
            )

            # Start compression
            if LOG_CHANNEL and download_start:
                try:
                    await download_start.delete()
                    utc_now = datetime.datetime.utcnow()
                    ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
                    ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
                    
                    compress_start = await bot.send_message(
                        LOG_CHANNEL,
                        f"🎬 **Compressing Video...** \\n\\n"
                        f"👤 **User:** {update.from_user.first_name} ({update.from_user.id})\\n"
                        f"⏱️ **Duration:** {TimeFormatter(duration * 1000)}\\n"
                        f"🎯 **Target:** {target_percentage}%\\n"
                        f"⏰ **Started:** `{ist}` (GMT+05:30)",
                        parse_mode="markdown"
                    )
                except:
                    compress_start = None
            else:
                compress_start = None

            await sent_message.edit_text(Localisation.COMPRESS_START)

            c_start = time.time()
            
            # Compress video
            compressed_file = await convert_video(
                saved_file_path,
                DOWNLOAD_LOCATION,
                duration,
                bot,
                sent_message,
                target_percentage,
                isAuto,
                compress_start
            )

            compressed_time = TimeFormatter((time.time() - c_start) * 1000)
            
            LOGGER.info(f"Compression result: {compressed_file}")

            if compressed_file is not None:
                # Upload compressed file
                if LOG_CHANNEL and compress_start:
                    try:
                        await compress_start.delete()
                        utc_now = datetime.datetime.utcnow()
                        ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
                        ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
                        
                        upload_start = await bot.send_message(
                            LOG_CHANNEL,
                            f"📤 **Uploading Video...** \\n\\n"
                            f"👤 **User:** {update.from_user.first_name} ({update.from_user.id})\\n"
                            f"⏰ **Started:** `{ist}` (GMT+05:30)",
                            parse_mode="markdown"
                        )
                    except:
                        upload_start = None
                else:
                    upload_start = None

                await sent_message.edit_text(Localisation.UPLOAD_START)

                u_start = time.time()
                
                caption = Localisation.get_compress_success().format(
                    downloaded_time, compressed_time, "{}"
                )

                upload = await bot.send_video(
                    chat_id=update.chat.id,
                    video=compressed_file,
                    caption=caption,
                    supports_streaming=True,
                    duration=int(duration),
                    thumb=thumb_image_path,
                    reply_to_message_id=update.id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        bot,
                        Localisation.UPLOAD_START,
                        sent_message,
                        u_start
                    )
                )

                if upload is not None:
                    uploaded_time = TimeFormatter((time.time() - u_start) * 1000)
                    
                    # Update caption with upload time
                    try:
                        await upload.edit_caption(
                            caption=upload.caption.format(uploaded_time)
                        )
                    except:
                        pass

                    # Update user stats
                    if db:
                        try:
                            original_size = os.path.getsize(saved_file_path)
                            compressed_size = os.path.getsize(compressed_file)
                            await db.increment_user_compression(update.from_user.id, original_size)
                        except:
                            pass

                    # Success log
                    if LOG_CHANNEL and upload_start:
                        try:
                            await upload_start.delete()
                            utc_now = datetime.datetime.utcnow()
                            ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
                            ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
                            
                            await bot.send_message(
                                LOG_CHANNEL,
                                f"✅ **Upload Completed!** \\n\\n"
                                f"👤 **User:** {update.from_user.first_name} ({update.from_user.id})\\n"
                                f"⏰ **Completed:** `{ist}` (GMT+05:30)\\n"
                                f"📊 **Total Time:** {TimeFormatter((time.time() - d_start) * 1000)}\\n\\n"
                                f"🎉 **Bot is Free Now!**",
                                parse_mode="markdown"
                            )
                        except:
                            pass

                    await sent_message.delete()
                    
                else:
                    await cleanup_process(update.from_user.id, sent_message, upload_start, "Upload failed")
                    return
            else:
                await cleanup_process(update.from_user.id, sent_message, compress_start, "Compression failed")
                return
        else:
            await cleanup_process(update.from_user.id, sent_message, download_start, "Downloaded file not found")
            return

        # Cleanup
        await cleanup_files_and_process(update.from_user.id, [saved_file_path, compressed_file, thumb_image_path])

    except Exception as e:
        LOGGER.error(f"Error in compress handler: {e}")
        if update.from_user.id in CURRENT_PROCESSES:
            del CURRENT_PROCESSES[update.from_user.id]
        await delete_downloads()
        await update.reply_text("❌ An error occurred during compression. Please try again later.")

async def incoming_cancel_message_f(bot: Client, update: Message):
    """Enhanced /cancel command handler"""
    try:
        if update.from_user.id not in AUTH_USERS:
            await update.reply_text("❌ You don't have permission to use this command.")
            return

        status = DOWNLOAD_LOCATION + "/status.json"
        
        if os.path.exists(status):
            # Show confirmation
            await update.reply_text(
                "🗑️ **Cancel Current Process?**\\n\\n"
                "⚠️ This will stop the current compression!\\n"
                "❌ This action cannot be undone!",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton('✅ Yes, Cancel', callback_data='confirm_cancel'),
                        InlineKeyboardButton('❌ No, Keep', callback_data='keep_process')
                    ]
                ])
            )
        else:
            await update.reply_text("❌ No active compression process found.")

    except Exception as e:
        LOGGER.error(f"Error in cancel handler: {e}")
        await update.reply_text("❌ An error occurred.")

# Helper functions
async def check_subscription(bot: Client, update: Message) -> bool:
    """Check if user is subscribed to updates channel"""
    try:
        user = await bot.get_chat_member(UPDATES_CHANNEL, update.from_user.id)
        if user.status == "kicked":
            await update.reply_text(
                "🚫 **You are banned from the updates channel.**\\n"
                "📞 Contact support group for assistance.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton('💬 Support Group', url='https://t.me/linux_repo')
                ]])
            )
            return False
    except UserNotParticipant:
        await update.reply_text(
            "📢 **Please join our updates channel to use this bot!**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    '🔗 Join Updates Channel', 
                    url=f'https://t.me/{UPDATES_CHANNEL}'
                )
            ]])
        )
        return False
    except Exception as e:
        LOGGER.error(f"Error checking subscription: {e}")
        await update.reply_text(
            "❌ **Unable to verify subscription status.**\\n"
            "📞 Contact support if this persists.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton('💬 Support Group', url='https://t.me/linux_repo')
            ]])
        )
        return False
    
    return True

async def validate_video_file(video, update: Message) -> bool:
    """Validate video file for compression"""
    # Check file size
    if video.file_size > TG_MAX_FILE_SIZE:
        max_size_mb = TG_MAX_FILE_SIZE // (1024 * 1024)
        await update.reply_text(
            Localisation.ERROR_MESSAGES['file_too_large'].format(max_size_mb)
        )
        return False
    
    # Check file extension if filename is available
    if hasattr(video, 'file_name') and video.file_name:
        if not ValidationUtils.validate_file_extension(video.file_name, ALLOWED_FILE_TYPES):
            await update.reply_text(Localisation.ERROR_MESSAGES['invalid_file'])
            return False
    
    return True

async def cleanup_process(user_id: int, sent_message, log_message, reason: str):
    """Cleanup failed process"""
    try:
        if user_id in CURRENT_PROCESSES:
            del CURRENT_PROCESSES[user_id]
        
        await sent_message.edit_text(f"❌ **Process Failed**\\n\\n🔍 **Reason:** {reason}")
        
        if log_message:
            try:
                await log_message.delete()
                if LOG_CHANNEL:
                    await sent_message._client.send_message(
                        LOG_CHANNEL,
                        f"❌ **Process Failed - Bot is Free Now!**\\n\\n"
                        f"🔍 **Reason:** {reason}",
                        parse_mode="markdown"
                    )
            except:
                pass
        
        await delete_downloads()
        
    except Exception as e:
        LOGGER.error(f"Cleanup error: {e}")

async def cleanup_files_and_process(user_id: int, files: list):
    """Cleanup files and process"""
    try:
        # Remove user from active processes
        if user_id in CURRENT_PROCESSES:
            del CURRENT_PROCESSES[user_id]
        
        # Remove files
        for file_path in files:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
        
        # Clean status file
        status = DOWNLOAD_LOCATION + "/status.json"
        if os.path.exists(status):
            try:
                os.remove(status)
            except:
                pass
        
        # General cleanup
        await delete_downloads()
        
    except Exception as e:
        LOGGER.error(f"File cleanup error: {e}")

print("Created enhanced incoming message handler")
