#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# FINAL FIXED - Enhanced Callback Button Handler with Button System Support
# Combines working callback handlers with button-based compression system

import logging
import os
import json
import time
from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode

from bot.localisation import Localisation
from bot import DOWNLOAD_LOCATION, AUTH_USERS

try:
    from bot.database import Database
    from bot import DATABASE_URL, SESSION_NAME
    db = Database(DATABASE_URL, SESSION_NAME) if DATABASE_URL else None
except:
    db = None

from bot.helper_funcs.utils import delete_downloads
from bot.helper_funcs.display_progress import humanbytes

LOGGER = logging.getLogger(__name__)

async def button(bot: Client, update: CallbackQuery):
    """Enhanced callback query handler with button system support"""
    try:
        cb_data = update.data
        user_id = update.from_user.id
        
        LOGGER.info(f"Callback from user {user_id}: {cb_data}")

        # ✅ BUTTON SYSTEM: Quality selection callbacks
        if cb_data.startswith('quality_'):
            quality = cb_data.replace('quality_', '')
            if quality == "custom":
                await handle_custom_quality_selection(bot, update)
            else:
                await handle_quality_selection(bot, update, quality)

        # ✅ BUTTON SYSTEM: Encoding settings callbacks
        elif cb_data.startswith('setting_'):
            setting_type = cb_data.replace('setting_', '')
            await handle_encoding_setting(bot, update, setting_type)

        # ✅ BUTTON SYSTEM: Setting value callbacks
        elif cb_data.startswith('set_'):
            await handle_setting_value_change(bot, update, cb_data)

        # ✅ BUTTON SYSTEM: Navigation callbacks
        elif cb_data == 'back_to_quality':
            await show_quality_selection(bot, update)
        
        elif cb_data == 'back_to_encoding':
            await show_encoding_settings(bot, update)

        # ✅ BUTTON SYSTEM: Compression control callbacks
        elif cb_data == 'start_encoding':
            await start_compression_process(bot, update)

        elif cb_data == 'cancel_compression':
            await handle_compression_cancel(bot, update)

        elif cb_data == 'confirm_cancel':
            await confirm_cancel_compression(bot, update)

        elif cb_data == 'keep_process':
            await update.answer("✅ Process continued.", show_alert=True)

        # ✅ LEGACY: Basic navigation callbacks
        elif cb_data == "help":
            await update.message.edit_text(
                Localisation.HELP_MESSAGE,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="start")
                ]])
            )

        elif cb_data == "settings":
            await show_user_settings(bot, update)

        elif cb_data == "status":
            await show_bot_status(bot, update)

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

        # ✅ LEGACY: Admin callbacks
        elif cb_data == "refresh_status":
            await show_bot_status(bot, update)

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

# ✅ BUTTON SYSTEM: Quality selection handlers

async def handle_quality_selection(bot: Client, callback_query, quality: str):
    """Handle quality selection from button system"""
    try:
        # Import here to avoid circular imports
        from bot.plugins.incoming_message_fn import handle_quality_selection
        await handle_quality_selection(bot, callback_query, quality)
    except Exception as e:
        LOGGER.error(f"Error in quality selection: {e}")
        await callback_query.answer("❌ An error occurred.", show_alert=True)

async def handle_custom_quality_selection(bot: Client, callback_query):
    """Handle custom quality selection"""
    try:
        from bot.plugins.incoming_message_fn import USER_SESSIONS
        user_id = callback_query.from_user.id
        
        if user_id not in USER_SESSIONS:
            await callback_query.answer("❌ Session expired. Please send video again.", show_alert=True)
            return

        session = USER_SESSIONS[user_id]
        session.quality = "custom"

        # Show resolution selection for custom quality
        resolution_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton('🔥 4K (3840x2160)', callback_data='set_resolution_3840x2160'),
                InlineKeyboardButton('📺 1440p (2560x1440)', callback_data='set_resolution_2560x1440')
            ],
            [
                InlineKeyboardButton('🎬 1080p (1920x1080)', callback_data='set_resolution_1920x1080'),
                InlineKeyboardButton('📱 720p (1280x720)', callback_data='set_resolution_1280x720')
            ],
            [
                InlineKeyboardButton('📱 480p (854x480)', callback_data='set_resolution_854x480'),
                InlineKeyboardButton('📱 360p (640x360)', callback_data='set_resolution_640x360')
            ],
            [
                InlineKeyboardButton('🔄 Keep Original', callback_data='set_resolution_original'),
                InlineKeyboardButton('🔙 Back', callback_data='back_to_quality')
            ]
        ])

        await callback_query.edit_message_text(
            f"⚙️ **Custom Quality Selected**\n\n"
            f"📏 **Select Output Resolution:**\n\n"
            f"🔹 Higher resolution = Better quality + Larger file\n"
            f"🔹 Lower resolution = Faster encoding + Smaller file\n"
            f"🔹 Original = Keep source resolution",
            reply_markup=resolution_keyboard
        )

    except Exception as e:
        LOGGER.error(f"Error in custom quality selection: {e}")
        await callback_query.answer("❌ An error occurred.", show_alert=True)

async def handle_encoding_setting(bot: Client, callback_query, setting_type: str):
    """Handle encoding setting adjustment"""
    try:
        from bot.plugins.incoming_message_fn import USER_SESSIONS
        user_id = callback_query.from_user.id
        
        if user_id not in USER_SESSIONS:
            await callback_query.answer("❌ Session expired. Please send video again.", show_alert=True)
            return

        session = USER_SESSIONS[user_id]

        if setting_type == 'crf':
            crf_keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('15 (Best)', callback_data='set_crf_15'),
                    InlineKeyboardButton('18 (High)', callback_data='set_crf_18'),
                    InlineKeyboardButton('20 (Good)', callback_data='set_crf_20')
                ],
                [
                    InlineKeyboardButton('23 (Medium)', callback_data='set_crf_23'),
                    InlineKeyboardButton('26 (Lower)', callback_data='set_crf_26'),
                    InlineKeyboardButton('30 (Lowest)', callback_data='set_crf_30')
                ],
                [
                    InlineKeyboardButton('🔙 Back', callback_data='back_to_encoding')
                ]
            ])
            
            await callback_query.edit_message_text(
                f"🎛️ **CRF Quality Control**\n\n"
                f"📊 **Current:** {session.crf}\n\n"
                f"🔹 **Lower CRF** = Better quality, larger file\n"
                f"🔹 **Higher CRF** = Lower quality, smaller file\n"
                f"🔹 **Recommended:** 18-26 range\n\n"
                f"💡 **Select CRF value:**",
                reply_markup=crf_keyboard
            )

        elif setting_type == 'audio_bitrate':
            audio_keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('64k', callback_data='set_audio_bitrate_64k'),
                    InlineKeyboardButton('96k', callback_data='set_audio_bitrate_96k'),
                    InlineKeyboardButton('128k', callback_data='set_audio_bitrate_128k')
                ],
                [
                    InlineKeyboardButton('192k', callback_data='set_audio_bitrate_192k'),
                    InlineKeyboardButton('256k', callback_data='set_audio_bitrate_256k'),
                    InlineKeyboardButton('Copy', callback_data='set_audio_bitrate_copy')
                ],
                [
                    InlineKeyboardButton('🔙 Back', callback_data='back_to_encoding')
                ]
            ])
            
            await callback_query.edit_message_text(
                f"🎵 **Audio Bitrate Setting**\n\n"
                f"📊 **Current:** {session.audio_bitrate}\n\n"
                f"🔹 **64k-96k:** Low quality, small file\n"
                f"🔹 **128k:** Standard quality (recommended)\n"
                f"🔹 **192k-256k:** High quality\n"
                f"🔹 **Copy:** Keep original (fastest)\n\n"
                f"💡 **Select audio bitrate:**",
                reply_markup=audio_keyboard
            )

        elif setting_type == 'preset':
            preset_keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('ultrafast', callback_data='set_preset_ultrafast'),
                    InlineKeyboardButton('superfast', callback_data='set_preset_superfast')
                ],
                [
                    InlineKeyboardButton('veryfast', callback_data='set_preset_veryfast'),
                    InlineKeyboardButton('faster', callback_data='set_preset_faster')
                ],
                [
                    InlineKeyboardButton('fast', callback_data='set_preset_fast'),
                    InlineKeyboardButton('medium', callback_data='set_preset_medium')
                ],
                [
                    InlineKeyboardButton('slow', callback_data='set_preset_slow'),
                    InlineKeyboardButton('slower', callback_data='set_preset_slower')
                ],
                [
                    InlineKeyboardButton('🔙 Back', callback_data='back_to_encoding')
                ]
            ])
            
            await callback_query.edit_message_text(
                f"⚡ **Encoding Preset**\n\n"
                f"📊 **Current:** {session.preset}\n\n"
                f"🔹 **Faster presets** = Quick encoding, larger file\n"
                f"🔹 **Slower presets** = Better compression, smaller file\n"
                f"🔹 **Recommended:** medium, slow\n\n"
                f"💡 **Select preset:**",
                reply_markup=preset_keyboard
            )

        elif setting_type == 'video_codec':
            codec_keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('libx264 (H.264)', callback_data='set_video_codec_libx264'),
                    InlineKeyboardButton('libx265 (H.265)', callback_data='set_video_codec_libx265')
                ],
                [
                    InlineKeyboardButton('🔙 Back', callback_data='back_to_encoding')
                ]
            ])
            
            await callback_query.edit_message_text(
                f"🎬 **Video Codec Selection**\n\n"
                f"📊 **Current:** {session.video_codec}\n\n"
                f"🔹 **libx264 (H.264):** Universal compatibility\n"
                f"🔹 **libx265 (H.265):** Better compression, smaller files\n\n"
                f"💡 **Select video codec:**",
                reply_markup=codec_keyboard
            )

        elif setting_type == 'audio_codec':
            audio_codec_keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('AAC', callback_data='set_audio_codec_aac'),
                    InlineKeyboardButton('MP3', callback_data='set_audio_codec_mp3')
                ],
                [
                    InlineKeyboardButton('Copy Original', callback_data='set_audio_codec_copy'),
                    InlineKeyboardButton('🔙 Back', callback_data='back_to_encoding')
                ]
            ])
            
            await callback_query.edit_message_text(
                f"🎵 **Audio Codec Selection**\n\n"
                f"📊 **Current:** {session.audio_codec}\n\n"
                f"🔹 **AAC:** Best quality and compatibility\n"
                f"🔹 **MP3:** Universal support\n"
                f"🔹 **Copy:** Keep original (fastest)\n\n"
                f"💡 **Select audio codec:**",
                reply_markup=audio_codec_keyboard
            )

        elif setting_type == 'pixel_format':
            pixel_keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('yuv420p', callback_data='set_pixel_format_yuv420p'),
                    InlineKeyboardButton('yuv444p', callback_data='set_pixel_format_yuv444p')
                ],
                [
                    InlineKeyboardButton('🔙 Back', callback_data='back_to_encoding')
                ]
            ])
            
            await callback_query.edit_message_text(
                f"🎨 **Pixel Format Setting**\n\n"
                f"📊 **Current:** {session.pixel_format}\n\n"
                f"🔹 **yuv420p:** Standard (recommended)\n"
                f"🔹 **yuv444p:** Higher quality colors\n\n"
                f"💡 **Select pixel format:**",
                reply_markup=pixel_keyboard
            )

    except Exception as e:
        LOGGER.error(f"Error in encoding setting: {e}")
        await callback_query.answer("❌ An error occurred.", show_alert=True)

async def handle_setting_value_change(bot: Client, callback_query, cb_data: str):
    """Handle specific setting value changes"""
    try:
        from bot.plugins.incoming_message_fn import USER_SESSIONS
        user_id = callback_query.from_user.id
        
        if user_id not in USER_SESSIONS:
            await callback_query.answer("❌ Session expired. Please send video again.", show_alert=True)
            return

        session = USER_SESSIONS[user_id]

        # Parse callback data and update session
        if cb_data.startswith('set_crf_'):
            crf_value = int(cb_data.replace('set_crf_', ''))
            session.crf = crf_value
            await callback_query.answer(f"✅ CRF set to {crf_value}")

        elif cb_data.startswith('set_audio_bitrate_'):
            bitrate = cb_data.replace('set_audio_bitrate_', '')
            session.audio_bitrate = bitrate
            if bitrate == "copy":
                session.audio_codec = "copy"
            await callback_query.answer(f"✅ Audio bitrate set to {bitrate}")

        elif cb_data.startswith('set_preset_'):
            preset = cb_data.replace('set_preset_', '')
            session.preset = preset
            await callback_query.answer(f"✅ Preset set to {preset}")

        elif cb_data.startswith('set_video_codec_'):
            codec = cb_data.replace('set_video_codec_', '')
            session.video_codec = codec
            await callback_query.answer(f"✅ Video codec set to {codec}")

        elif cb_data.startswith('set_audio_codec_'):
            codec = cb_data.replace('set_audio_codec_', '')
            session.audio_codec = codec
            await callback_query.answer(f"✅ Audio codec set to {codec}")

        elif cb_data.startswith('set_pixel_format_'):
            pixel_format = cb_data.replace('set_pixel_format_', '')
            session.pixel_format = pixel_format
            await callback_query.answer(f"✅ Pixel format set to {pixel_format}")

        elif cb_data.startswith('set_resolution_'):
            resolution = cb_data.replace('set_resolution_', '')
            if resolution == 'original':
                session.resolution = None
                await callback_query.answer("✅ Resolution set to Original")
            else:
                session.resolution = resolution
                await callback_query.answer(f"✅ Resolution set to {resolution}")

        # Return to encoding settings after change
        await show_encoding_settings(bot, callback_query)

    except Exception as e:
        LOGGER.error(f"Error changing setting value: {e}")
        await callback_query.answer("❌ An error occurred.", show_alert=True)

async def show_quality_selection(bot: Client, callback_query):
    """Show quality selection menu"""
    try:
        from bot.plugins.incoming_message_fn import USER_SESSIONS
        from bot.helper_funcs.display_progress import humanbytes, TimeFormatter
        user_id = callback_query.from_user.id
        
        if user_id not in USER_SESSIONS:
            await callback_query.answer("❌ Session expired. Please send video again.", show_alert=True)
            return

        session = USER_SESSIONS[user_id]
        video_message = session.video_message
        video = video_message.video or video_message.document

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

        await callback_query.edit_message_text(
            f"🎬 **Video Received!**\n\n"
            f"📄 **File:** {video.file_name or 'Unknown'}\n"
            f"📏 **Size:** {humanbytes(video.file_size)}\n"
            f"⏱️ **Duration:** {TimeFormatter((video.duration or 0) * 1000)}\n\n"
            f"🎯 **Select Compression Quality:**",
            reply_markup=quality_keyboard
        )

    except Exception as e:
        LOGGER.error(f"Error showing quality selection: {e}")
        await callback_query.answer("❌ An error occurred.", show_alert=True)

async def show_encoding_settings(bot: Client, callback_query):
    """Show encoding settings menu"""
    try:
        from bot.plugins.incoming_message_fn import show_encoding_settings
        await show_encoding_settings(bot, callback_query)
    except Exception as e:
        LOGGER.error(f"Error showing encoding settings: {e}")
        await callback_query.answer("❌ An error occurred.", show_alert=True)

async def start_compression_process(bot: Client, callback_query):
    """Start compression process with button system"""
    try:
        from bot.plugins.incoming_message_fn import start_compression_process
        await start_compression_process(bot, callback_query)
    except Exception as e:
        LOGGER.error(f"Error starting compression: {e}")
        await callback_query.answer("❌ An error occurred.", show_alert=True)

# ✅ LEGACY: Working status and settings functions

async def show_user_settings(bot: Client, update: CallbackQuery):
    """Show user settings menu"""
    try:
        if not db:
            await update.message.edit_text(
                "❌ **Settings Unavailable**\n\n"
                "Database is not configured for this bot.\n"
                "Contact admin for assistance."
            )
            return

        user_settings = await db.get_user_settings(update.from_user.id)
        
        settings_text = (
            f"⚙️ **Your Settings**\n\n"
            f"🎨 **Default Quality:** {user_settings.get('default_quality', 50)}%\n"
            f"📱 **Output Format:** {user_settings.get('output_format', 'MP4').upper()}\n"
            f"🖼️ **Custom Thumbnail:** {'✅ Set' if user_settings.get('custom_thumbnail') else '❌ None'}\n"
            f"📊 **Progress Updates:** {'✅ Enabled' if user_settings.get('progress_updates', True) else '❌ Disabled'}\n"
            f"🔔 **Notifications:** {'✅ Enabled' if user_settings.get('notifications', True) else '❌ Disabled'}\n\n"
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
        from bot.helper_funcs.utils import SystemUtils
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
            f"📊 **Enhanced VideoCompress Bot Status**\n\n"
            f"🤖 **Bot Status:** {'🟢 Online' if bot.is_connected else '🔴 Offline'}\n"
            f"⚙️ **Active Processes:** {active_processes}\n"
        )

        if db:
            try:
                total_users = await db.total_users_count()
                active_users = await db.active_users_count()
                status_text += f"👥 **Total Users:** {total_users:,}\n"
                status_text += f"🟢 **Active Users (7d):** {active_users:,}\n"
            except:
                status_text += f"👥 **Users:** Database error\n"
        else:
            status_text += f"👥 **Users:** Database not configured\n"

        status_text += (
            f"\n**💻 System Resources:**\n"
            f"🔥 **CPU:** {system_info.get('cpu_percent', 0):.1f}%\n"
            f"💾 **Memory:** {system_info.get('memory_percent', 0):.1f}%\n"
            f"💿 **Disk:** {system_info.get('disk_percent', 0):.1f}%\n"
        )

        if system_info.get('memory_available', 0) > 0:
            status_text += f"🆓 **Free Memory:** {humanbytes(system_info['memory_available'])}\n"
        if system_info.get('disk_free', 0) > 0:
            status_text += f"💾 **Free Disk:** {humanbytes(system_info['disk_free'])}\n"

        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh_status"),
            ]
        ]

        if update.from_user.id in AUTH_USERS:
            keyboard.append([
                InlineKeyboardButton("🧹 Clean Downloads", callback_data="clean_downloads"),
            ])

        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="start")])

        await update.message.edit_text(
            status_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        LOGGER.error(f"Status display error: {e}")
        await update.message.edit_text("❌ Error loading status")

async def handle_compression_cancel(bot: Client, update: CallbackQuery):
    """Handle compression cancellation request"""
    try:
        await update.message.edit_text(
            "🗑️ **Cancel Compression Process?**\n\n"
            "⚠️ This will stop the current compression job\n"
            "❌ This action cannot be undone!\n\n"
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
        from bot.plugins.incoming_message_fn import CURRENT_PROCESSES, USER_SESSIONS
        user_id = update.from_user.id

        # Cancel active process
        if user_id in CURRENT_PROCESSES:
            del CURRENT_PROCESSES[user_id]

        # Clean up session
        if user_id in USER_SESSIONS:
            del USER_SESSIONS[user_id]

        status_file = DOWNLOAD_LOCATION + "/status.json"
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r') as f:
                    status_data = json.load(f)
                
                pid = status_data.get('pid')
                if pid:
                    # Try to kill the process
                    try:
                        import signal
                        os.kill(pid, signal.SIGTERM)
                        result_text = "✅ **Compression Cancelled Successfully!**"
                    except:
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
            f"{result_text}\n\n"
            f"🧹 Temporary files cleaned up\n"
            f"✨ Bot is ready for new compressions"
        )

    except Exception as e:
        LOGGER.error(f"Cancel confirmation error: {e}")
        await update.message.edit_text("❌ Error during cancellation")

async def clean_downloads_callback(bot: Client, update: CallbackQuery):
    """Clean downloads via callback"""
    try:
        await update.message.edit_text("🧹 **Cleaning downloads...**")
        
        # Simple cleanup
        await delete_downloads()
        
        await update.message.edit_text(
            f"✅ **Cleanup Completed!**\n\n"
            f"💾 **Download directory cleaned**\n\n"
            f"✨ Ready for new compressions!"
        )

    except Exception as e:
        LOGGER.error(f"Clean downloads callback error: {e}")
        await update.message.edit_text("❌ Error during cleanup")
