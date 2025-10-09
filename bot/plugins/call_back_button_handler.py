#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# FIXED Enhanced Incoming Message Handler with Button System + Working Log Channel Updates
# Combines button-based compression system with proper log channel updates

import datetime
import logging
import os
import time
import asyncio
import json
from typing import Optional, Dict, Any
from pyrogram.enums import ParseMode
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

# Track current processes and user sessions
CURRENT_PROCESSES = {}
USER_SESSIONS = {}

class CompressionSettings:
    """Store user's compression settings"""
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.video_message = None
        self.quality = None
        self.resolution = None
        self.video_codec = "libx264"
        self.audio_codec = "aac"
        self.preset = "medium"
        self.crf = 23
        self.audio_bitrate = "128k"
        self.pixel_format = "yuv420p"
        self.created_at = time.time()

# Quality presets mapping
QUALITY_PRESETS = {
    "1080p": {"resolution": "1920x1080", "crf": 18, "preset": "slow"},
    "1080p_hevc": {"resolution": "1920x1080", "crf": 20, "preset": "medium", "codec": "libx265"},
    "720p": {"resolution": "1280x720", "crf": 20, "preset": "medium"},
    "720p_hevc": {"resolution": "1280x720", "crf": 22, "preset": "medium", "codec": "libx265"},
    "480p": {"resolution": "854x480", "crf": 23, "preset": "fast"},
    "480p_hevc": {"resolution": "854x480", "crf": 25, "preset": "fast", "codec": "libx265"},
    "custom": {"crf": 23, "preset": "medium"}
}

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
            parse_mode=ParseMode.HTML,
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

async def handle_video_message(bot: Client, update: Message):
    """Handle incoming video messages and show quality selection buttons"""
    try:
        # Check if user exists and update activity
        if db and not await db.is_user_exist(update.from_user.id):
            await db.add_user(
                update.from_user.id,
                update.from_user.username,
                update.from_user.first_name
            )

        if db:
            await db.update_user_activity(update.from_user.id)

        # Check subscription
        if UPDATES_CHANNEL and not await check_subscription(bot, update):
            return

        # Validate video file
        video = update.video or update.document
        if not video:
            return

        if not await validate_video_file(video, update):
            return

        # Check if user has active process
        if update.from_user.id in CURRENT_PROCESSES:
            await update.reply_text(
                "⚠️ You already have a compression in progress!\n"
                "⏰ Please wait for it to complete."
            )
            return

        # Store video message in user session
        session = CompressionSettings(update.from_user.id)
        session.video_message = update
        USER_SESSIONS[update.from_user.id] = session

        # Send quality selection keyboard
        quality_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton('🔥 1080p', callback_data='quality_1080p'),
                InlineKeyboardButton('🔥 1080p HEVC', callback_data='quality_1080p_hevc')
            ],
            [
                InlineKeyboardButton('⭐ 720p', callback_data='quality_720p'),
                InlineKeyboardButton('⭐ 720p HEVC', callback_data='quality_720p_hevc')
            ],
            [
                InlineKeyboardButton('📱 480p', callback_data='quality_480p'),
                InlineKeyboardButton('📱 480p HEVC', callback_data='quality_480p_hevc')
            ],
            [
                InlineKeyboardButton('⚙️ Custom +', callback_data='quality_custom'),
                InlineKeyboardButton('❌ Cancel', callback_data='cancel_compression')
            ]
        ])

        await update.reply_text(
            f"🎬 **Video Received!**\n\n"
            f"📄 **File:** {video.file_name or 'Unknown'}\n"
            f"📏 **Size:** {humanbytes(video.file_size)}\n"
            f"⏱️ **Duration:** {TimeFormatter((video.duration or 0) * 1000)}\n\n"
            f"🎯 **Select Compression Quality:**",
            reply_markup=quality_keyboard
        )

    except Exception as e:
        LOGGER.error(f"Error handling video message: {e}")
        await update.reply_text("❌ An error occurred while processing your video.")

async def start_compression_process(bot: Client, callback_query):
    """Start the actual compression process with FULL LOG CHANNEL SUPPORT"""
    try:
        user_id = callback_query.from_user.id
        
        if user_id not in USER_SESSIONS:
            await callback_query.answer("❌ Session expired. Please send video again.", show_alert=True)
            return

        if user_id in CURRENT_PROCESSES:
            await callback_query.answer("❌ You already have an active compression!", show_alert=True)
            return

        session = USER_SESSIONS[user_id]
        video_message = session.video_message
        video = video_message.video or video_message.document

        # Mark user as having active process
        CURRENT_PROCESSES[user_id] = True

        # Generate file paths
        user_file = f"{user_id}_{int(time.time())}.mkv"
        saved_file_path = os.path.join(DOWNLOAD_LOCATION, user_file)

        # Start timing
        d_start = time.time()
        
        # Update message to show compression started
        sent_message = await callback_query.edit_message_text(
            f"🚀 **Encoding Started!**\n\n"
            f"⚙️ **Settings:**\n"
            f"🔹 **Quality:** {session.quality}\n"
            f"🔹 **CRF:** {session.crf}\n"
            f"🔹 **Preset:** {session.preset}\n"
            f"🔹 **Resolution:** {session.resolution or 'Original'}\n"
            f"🔹 **Codec:** {session.video_codec}\n\n"
            f"📥 **Starting download...**"
        )

        # ========== LOG CHANNEL: Download Start ==========
        download_start = None
        if LOG_CHANNEL:
            try:
                utc_now = datetime.datetime.utcnow()
                ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
                ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
                
                download_start = await bot.send_message(
                    LOG_CHANNEL,
                    f"🔥 **Bot Busy Now!** \n\n"
                    f"👤 **User:** {callback_query.from_user.first_name} ({callback_query.from_user.id})\n"
                    f"📁 **File:** {video.file_name or 'Unknown'}\n"
                    f"📏 **Size:** {humanbytes(video.file_size)}\n"
                    f"🎯 **Quality:** {session.quality}\n"
                    f"🔹 **CRF:** {session.crf}\n"
                    f"🔹 **Codec:** {session.video_codec}\n"
                    f"⏰ **Started:** `{ist}` (GMT+05:30)",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                LOGGER.warning(f"Could not send download start log: {e}")

        # Create status file for tracking
        status = os.path.join(DOWNLOAD_LOCATION, "status.json")
        status_data = {
            'running': True,
            'message': sent_message.id,
            'user_id': user_id
        }
        
        with open(status, 'w') as f:
            json.dump(status_data, f, indent=2)

        # Start download with progress
        try:
            video_download = await bot.download_media(
                message=video_message,
                file_name=saved_file_path,
                progress=progress_for_pyrogram,
                progress_args=(
                    "Downloading",
                    sent_message,
                    d_start,
                    bot
                )
            )

            if not video_download or not os.path.exists(video_download):
                await cleanup_process_with_logs(user_id, sent_message, download_start, "Download failed", bot)
                return

        except Exception as e:
            LOGGER.error(f"Download error: {e}")
            await cleanup_process_with_logs(user_id, sent_message, download_start, f"Download failed: {e}", bot)
            return

        # Get media info
        duration, bitrate = await media_info(saved_file_path)
        if duration is None:
            await cleanup_process_with_logs(user_id, sent_message, download_start, "Invalid video file", bot)
            return

        # Generate thumbnail
        thumb_image_path = await take_screen_shot(
            saved_file_path,
            os.path.dirname(saved_file_path),
            duration / 2
        )

        # ========== LOG CHANNEL: Compression Start ==========
        compress_start = None
        if LOG_CHANNEL and download_start:
            try:
                await download_start.delete()
                utc_now = datetime.datetime.utcnow()
                ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
                ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
                
                compress_start = await bot.send_message(
                    LOG_CHANNEL,
                    f"🎬 **Compressing Video...** \n\n"
                    f"👤 **User:** {callback_query.from_user.first_name} ({callback_query.from_user.id})\n"
                    f"⏱️ **Duration:** {TimeFormatter(duration * 1000)}\n"
                    f"🎯 **Quality:** {session.quality}\n"
                    f"🔹 **CRF:** {session.crf}\n"
                    f"🔹 **Preset:** {session.preset}\n"
                    f"🔹 **Codec:** {session.video_codec}\n"
                    f"⏰ **Started:** `{ist}` (GMT+05:30)",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                LOGGER.warning(f"Could not send compression start log: {e}")

        # Start compression
        await sent_message.edit_text(
            f"🎬 **Compressing Video...**\n\n"
            f"⚙️ **Using your settings:**\n"
            f"🔹 **Quality:** {session.quality}\n"
            f"🔹 **CRF:** {session.crf}\n"
            f"🔹 **Preset:** {session.preset}\n"
            f"⏳ **Please wait...**"
        )

        c_start = time.time()
        
        # Use custom compression with user settings - FIXED to pass session
        compressed_file = await convert_video_with_custom_settings(
            saved_file_path,
            DOWNLOAD_LOCATION,
            duration,
            bot,
            sent_message,
            session,
            compress_start  # Pass log message for updates
        )

        if not compressed_file or not os.path.exists(compressed_file):
            await cleanup_process_with_logs(user_id, sent_message, compress_start, "Compression failed", bot)
            return

        # ========== LOG CHANNEL: Upload Start ==========
        upload_start = None
        if LOG_CHANNEL and compress_start:
            try:
                await compress_start.delete()
                utc_now = datetime.datetime.utcnow()
                ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
                ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
                
                upload_start = await bot.send_message(
                    LOG_CHANNEL,
                    f"📤 **Uploading Video...** \n\n"
                    f"👤 **User:** {callback_query.from_user.first_name} ({callback_query.from_user.id})\n"
                    f"⏰ **Started:** `{ist}` (GMT+05:30)",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                LOGGER.warning(f"Could not send upload start log: {e}")

        # Upload compressed file
        await sent_message.edit_text(
            f"📤 **Uploading compressed video...**\n"
            f"⏳ **Please wait...**"
        )

        u_start = time.time()
        
        # Calculate compression stats
        original_size = os.path.getsize(saved_file_path)
        compressed_size = os.path.getsize(compressed_file)
        compression_ratio = ((original_size - compressed_size) / original_size) * 100

        # Create detailed caption
        downloaded_time = TimeFormatter((c_start - d_start) * 1000)
        compressed_time = TimeFormatter((time.time() - c_start) * 1000)

        caption = (
            f"✅ **Compression Completed!**\n\n"
            f"📊 **Statistics:**\n"
            f"🔹 **Original:** {humanbytes(original_size)}\n"
            f"🔹 **Compressed:** {humanbytes(compressed_size)}\n"
            f"🔹 **Saved:** {compression_ratio:.1f}%\n\n"
            f"⚙️ **Settings Used:**\n"
            f"🔹 **Quality:** {session.quality}\n"
            f"🔹 **CRF:** {session.crf}\n"
            f"🔹 **Codec:** {session.video_codec}\n"
            f"🔹 **Preset:** {session.preset}\n\n"
            f"⏱️ **Time Breakdown:**\n"
            f"📥 **Download:** {downloaded_time}\n"
            f"🎬 **Compress:** {compressed_time}\n"
            f"📤 **Upload:** {}\n\n"  # Upload time will be filled later
            f"🎉 **Total:** {TimeFormatter((time.time() - d_start) * 1000)}"
        )

        upload = await bot.send_video(
            chat_id=callback_query.message.chat.id,
            video=compressed_file,
            caption=caption,
            supports_streaming=True,
            duration=int(duration),
            thumb=thumb_image_path,
            reply_to_message_id=video_message.id,
            progress=progress_for_pyrogram,
            progress_args=(
                "Uploading",
                sent_message,
                u_start,
                bot
            )
        )

        if upload:
            # Update caption with upload time
            uploaded_time = TimeFormatter((time.time() - u_start) * 1000)
            
            try:
                await upload.edit_caption(
                    caption=upload.caption.format(uploaded_time)
                )
            except:
                pass

            # Update database stats
            if db:
                try:
                    await db.increment_user_compression(user_id, original_size)
                except:
                    pass

            # ========== LOG CHANNEL: Upload Complete ==========
            if LOG_CHANNEL and upload_start:
                try:
                    await upload_start.delete()
                    utc_now = datetime.datetime.utcnow()
                    ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
                    ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
                    
                    await bot.send_message(
                        LOG_CHANNEL,
                        f"✅ **Upload Completed!** \n\n"
                        f"👤 **User:** {callback_query.from_user.first_name} ({callback_query.from_user.id})\n"
                        f"⏰ **Completed:** `{ist}` (GMT+05:30)\n"
                        f"📊 **Stats:**\n"
                        f"🔹 **Original:** {humanbytes(original_size)}\n"
                        f"🔹 **Compressed:** {humanbytes(compressed_size)}\n"
                        f"🔹 **Saved:** {compression_ratio:.1f}%\n"
                        f"🔹 **Quality:** {session.quality} (CRF {session.crf})\n"
                        f"⏱️ **Total Time:** {TimeFormatter((time.time() - d_start) * 1000)}\n\n"
                        f"🎉 **Bot is Free Now!**",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    LOGGER.warning(f"Could not send upload complete log: {e}")

            # Delete progress message
            await sent_message.delete()
            
            # Log success
            LOGGER.info(f"Compression completed successfully for user {user_id}")

        # Cleanup
        await cleanup_files_and_process(user_id, [saved_file_path, compressed_file, thumb_image_path])

    except Exception as e:
        LOGGER.error(f"Error in compression process: {e}")
        if user_id in CURRENT_PROCESSES:
            del CURRENT_PROCESSES[user_id]
        if user_id in USER_SESSIONS:
            del USER_SESSIONS[user_id]
        await callback_query.message.edit_text("❌ An error occurred during compression.")

async def convert_video_with_custom_settings(video_file, output_directory, total_time, bot, message, session, log_message=None):
    """Convert video with custom settings from button system"""
    return await convert_video(
        video_file=video_file,
        output_directory=output_directory,
        total_time=total_time,
        bot=bot,
        message=message,
        target_percentage=f"{session.quality}_CRF{session.crf}",
        isAuto=False,
        bug=log_message
    )

# Keep existing legacy function for compatibility
async def incoming_compress_message_f(bot: Client, update: Message):
    """Legacy /compress command - now shows new system message"""
    await update.reply_text(
        "ℹ️ **New Button System Active!**\n\n"
        "🎬 Simply send me a video file and I'll show you quality options!\n"
        "📱 No need for /compress command anymore.\n\n"
        "✨ **New Features:**\n"
        "• Professional quality presets\n"
        "• Custom encoding settings\n"
        "• Real-time progress tracking\n"
        "• Detailed compression statistics"
    )

async def incoming_cancel_message_f(bot: Client, update: Message):
    """Enhanced /cancel command handler"""
    try:
        if update.from_user.id not in AUTH_USERS:
            await update.reply_text("❌ You don't have permission to use this command.")
            return

        user_id = update.from_user.id
        
        if user_id in CURRENT_PROCESSES or user_id in USER_SESSIONS:
            await update.reply_text(
                "🗑️ **Cancel Current Process?**\n\n"
                "⚠️ This will stop any active compression!\n"
                "❌ This action cannot be undone!",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton('✅ Yes, Cancel', callback_data='confirm_cancel'),
                        InlineKeyboardButton('❌ No, Keep', callback_data='keep_process')
                    ]
                ])
            )
        else:
            await update.reply_text("❌ No active process found.")

    except Exception as e:
        LOGGER.error(f"Error in cancel handler: {e}")
        await update.reply_text("❌ An error occurred.")

# Helper functions with LOG CHANNEL SUPPORT

async def cleanup_process_with_logs(user_id: int, sent_message, log_message, reason: str, bot: Client):
    """Enhanced cleanup with proper log channel updates"""
    try:
        if user_id in CURRENT_PROCESSES:
            del CURRENT_PROCESSES[user_id]
        
        if user_id in USER_SESSIONS:
            del USER_SESSIONS[user_id]

        await sent_message.edit_text(f"❌ **Process Failed**\n\n🔍 **Reason:** {reason}")

        # Send failure log to channel
        if LOG_CHANNEL:
            try:
                if log_message:
                    await log_message.delete()
                
                await bot.send_message(
                    LOG_CHANNEL,
                    f"❌ **Process Failed - Bot is Free Now!**\n\n"
                    f"👤 **User:** {sent_message.from_user.first_name if hasattr(sent_message, 'from_user') else 'Unknown'} ({user_id})\n"
                    f"🔍 **Reason:** {reason}\n"
                    f"⏰ **Time:** {datetime.datetime.utcnow().strftime('%d/%m/%Y, %H:%M:%S')} UTC",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                LOGGER.warning(f"Could not send failure log: {e}")

        await delete_downloads()

    except Exception as e:
        LOGGER.error(f"Cleanup error: {e}")

async def cleanup_files_and_process(user_id: int, files: list):
    """Cleanup files and process"""
    try:
        if user_id in CURRENT_PROCESSES:
            del CURRENT_PROCESSES[user_id]
        
        if user_id in USER_SESSIONS:
            del USER_SESSIONS[user_id]

        for file_path in files:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass

        # Clean up status file
        status = os.path.join(DOWNLOAD_LOCATION, "status.json")
        if os.path.exists(status):
            try:
                os.remove(status)
            except:
                pass

        await delete_downloads()

    except Exception as e:
        LOGGER.error(f"File cleanup error: {e}")

async def check_subscription(bot: Client, update: Message) -> bool:
    """Check if user is subscribed to updates channel"""
    try:
        user = await bot.get_chat_member(UPDATES_CHANNEL, update.from_user.id)
        if user.status == "kicked":
            await update.reply_text(
                "🚫 **You are banned from the updates channel.**\n"
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
        return False

    return True

async def validate_video_file(video, update: Message) -> bool:
    """Validate video file for compression"""
    if video.file_size > TG_MAX_FILE_SIZE:
        max_size_mb = TG_MAX_FILE_SIZE // (1024 * 1024)
        await update.reply_text(
            f"❌ **File too large!**\n\n"
            f"📏 **Size:** {humanbytes(video.file_size)}\n"
            f"🔢 **Limit:** {max_size_mb}MB"
        )
        return False

    if hasattr(video, 'file_name') and video.file_name:
        if not ValidationUtils.validate_file_extension(video.file_name, ALLOWED_FILE_TYPES):
            await update.reply_text("❌ **Unsupported file format!**")
            return False

    return True

# Quality handling functions for button system

async def handle_quality_selection(bot: Client, callback_query, quality: str):
    """Handle quality selection from user"""
    try:
        user_id = callback_query.from_user.id
        
        if user_id not in USER_SESSIONS:
            await callback_query.answer("❌ Session expired. Please send video again.", show_alert=True)
            return

        session = USER_SESSIONS[user_id]
        session.quality = quality

        # Set preset values based on quality selection
        if quality in QUALITY_PRESETS:
            preset = QUALITY_PRESETS[quality]
            session.resolution = preset.get("resolution")
            session.crf = preset["crf"]
            session.preset = preset["preset"]
            
            if "codec" in preset and preset["codec"] == "libx265":
                session.video_codec = "libx265"

        # Show encoding settings keyboard
        await show_encoding_settings(bot, callback_query)

    except Exception as e:
        LOGGER.error(f"Error in quality selection: {e}")
        await callback_query.answer("❌ An error occurred.", show_alert=True)

async def show_encoding_settings(bot: Client, callback_query):
    """Show encoding settings menu"""
    try:
        user_id = callback_query.from_user.id
        
        if user_id not in USER_SESSIONS:
            await callback_query.answer("❌ Session expired. Please send video again.", show_alert=True)
            return

        session = USER_SESSIONS[user_id]

        # Create encoding settings keyboard
        encoding_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f'CRF: {session.crf}', callback_data='setting_crf'),
                InlineKeyboardButton(f'Audio: {session.audio_bitrate}', callback_data='setting_audio_bitrate')
            ],
            [
                InlineKeyboardButton(f'Resolution: {session.resolution or "Original"}', callback_data='setting_resolution'),
                InlineKeyboardButton(f'Preset: {session.preset}', callback_data='setting_preset')
            ],
            [
                InlineKeyboardButton(f'Video Codec: {session.video_codec}', callback_data='setting_video_codec'),
                InlineKeyboardButton(f'Audio Codec: {session.audio_codec}', callback_data='setting_audio_codec')
            ],
            [
                InlineKeyboardButton(f'Pixel Format: {session.pixel_format}', callback_data='setting_pixel_format')
            ],
            [
                InlineKeyboardButton('🔙 Back', callback_data='back_to_quality'),
                InlineKeyboardButton('🚀 Start Encode', callback_data='start_encoding')
            ]
        ])

        quality_name = session.quality.replace('_', ' ').upper() if session.quality else "CUSTOM"
        
        await callback_query.edit_message_text(
            f"🎯 **Quality Selected:** {quality_name}\n\n"
            f"⚙️ **Current Encoding Settings:**\n"
            f"🔹 **CRF:** {session.crf} (Lower = Better Quality)\n"
            f"🔹 **Audio Bitrate:** {session.audio_bitrate}\n"
            f"🔹 **Resolution:** {session.resolution or 'Original'}\n"
            f"🔹 **Preset:** {session.preset} (Slower = Better Compression)\n"
            f"🔹 **Video Codec:** {session.video_codec}\n"
            f"🔹 **Audio Codec:** {session.audio_codec}\n"
            f"🔹 **Pixel Format:** {session.pixel_format}\n\n"
            f"📝 **Adjust settings or start encoding:**",
            reply_markup=encoding_keyboard
        )

    except Exception as e:
        LOGGER.error(f"Error showing encoding settings: {e}")
        await callback_query.answer("❌ An error occurred.", show_alert=True)
