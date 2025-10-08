# 5. bot/localisation.py - Enhanced localization

from bot.get_cfg import get_config
import random

class Localisation:
    """Enhanced localisation with multiple message variants"""
    
    # Welcome Messages
    START_TEXT = get_config(
        "START_TEXT",
        "🎬 <b>Welcome to Enhanced VideoCompress Bot v2.0!</b>\\n\\n"
        "🚀 <b>Features:</b>\\n"
        "• Advanced video compression with quality presets\\n"
        "• Multiple output formats (MP4, MKV, WEBM)\\n"
        "• Custom thumbnail support\\n"
        "• Queue management system\\n"
        "• Real-time progress tracking\\n"
        "• Batch processing support\\n\\n"
        "📖 Use /help to see all available commands\\n"
        "⚡️ Send any video file and use /compress to get started!"
    )
    
    HELP_MESSAGE = get_config(
        "HELP_MESSAGE",
        "📚 <b>Enhanced VideoCompress Bot v2.0 Help</b>\\n\\n"
        "<b>🔸 Public Commands:</b>\\n"
        "• <code>/start</code> - Start the bot\\n"
        "• <code>/help</code> - Show this help message\\n"
        "• <code>/compress [quality]</code> - Compress video (10-90)\\n"
        "• <code>/queue</code> - Check compression queue\\n"
        "• <code>/settings</code> - User settings\\n\\n"
        "<b>🔸 Usage Examples:</b>\\n"
        "• <code>/compress</code> - Auto compression\\n"
        "• <code>/compress 50</code> - 50% compression\\n"
        "• <code>/compress high</code> - High quality preset\\n"
        "• <code>/compress medium</code> - Medium quality preset\\n"
        "• <code>/compress low</code> - Low quality preset\\n\\n"
        "<b>📝 Note:</b> Reply to a video file with the compress command!"
    )
    
    # Process Messages
    DOWNLOAD_START = "📥 <b>Downloading video...</b>\\n⏳ Please wait while I fetch your file."
    UPLOAD_START = "📤 <b>Uploading compressed video...</b>\\n✨ Almost done!"
    COMPRESS_START = "🎬 <b>Compressing video...</b>\\n🔧 This may take a few minutes depending on file size."
    
    # Progress Messages
    COMPRESS_PROGRESS = "⏳ <b>ETA:</b> {}\\n🚀 <b>Progress:</b> {}%\\n📊 <b>Speed:</b> {}x"
    
    # Success Messages
    COMPRESS_SUCCESS_VARIANTS = [
        "✅ <b>Compression Complete!</b>\\n\\n📥 Downloaded in: {}\\n🎬 Compressed in: {}\\n📤 Uploaded in: {}\\n\\n🎯 <b>Enhanced VideoCompress Bot v2.0</b>",
        "🎉 <b>Video successfully compressed!</b>\\n\\n⏱️ Total time: {} + {} + {}\\n🔥 Thanks for using Enhanced VideoCompress Bot v2.0!",
        "🌟 <b>Compression job completed!</b>\\n\\nProcessing times:\\n📥 Download: {}\\n🎬 Compress: {}\\n📤 Upload: {}\\n\\n💎 Enhanced VideoCompress Bot v2.0"
    ]
    
    @classmethod
    def get_compress_success(cls):
        return random.choice(cls.COMPRESS_SUCCESS_VARIANTS)
    
    # Error Messages
    ERROR_MESSAGES = {
        'no_reply': "❌ <b>Please reply to a video file!</b>\\n📝 Send a video and reply with /compress",
        'invalid_file': "❌ <b>Invalid file format!</b>\\n✅ Supported: MP4, MKV, AVI, MOV, WEBM, FLV",
        'file_too_large': "❌ <b>File too large!</b>\\n📏 Maximum size: {} MB",
        'download_failed': "❌ <b>Download failed!</b>\\n🔄 Please try again later",
        'compress_failed': "❌ <b>Compression failed!</b>\\n💡 The video might be corrupted or unsupported",
        'upload_failed': "❌ <b>Upload failed!</b>\\n🔄 Please try again",
        'queue_full': "⏳ <b>Queue is full!</b>\\n⏰ Please wait and try again later",
        'process_exists': "⚠️ <b>You already have a compression in progress!</b>\\n⏳ Please wait for it to complete",
        'invalid_quality': "❌ <b>Invalid quality value!</b>\\n📊 Use values between 10-90 or presets: high, medium, low"
    }
    
    # Status Messages
    STATUS_MESSAGES = {
        'bot_started': "🚀 <b>Enhanced VideoCompress Bot v2.0 Started!</b>\\n✅ All systems operational",
        'bot_stopped': "⏹️ <b>Bot shutting down...</b>\\n💾 Saving all data",
        'queue_status': "📋 <b>Queue Status:</b>\\n👥 Active jobs: {}\\n⏳ Pending: {}\\n✅ Completed today: {}",
        'user_banned': "🚫 <b>User banned successfully!</b>\\n👤 User: {}\\n⏰ Duration: {}\\n📝 Reason: {}",
        'user_unbanned': "✅ <b>User unbanned successfully!</b>\\n👤 User: {}"
    }
    
    # Thumbnail Messages
    SAVED_CUSTOM_THUMB_NAIL = "✅ <b>Custom thumbnail saved!</b>\\n🖼️ This image will be used for your compressed videos."
    DEL_ETED_CUSTOM_THUMB_NAIL = "✅ <b>Custom thumbnail deleted!</b>\\n🔄 Default thumbnail will be used."
    NO_CUSTOM_THUMB_NAIL_FOUND = "❌ <b>No custom thumbnail found!</b>\\n💡 Send an image to set as thumbnail."
    
    # Admin Messages
    BROADCAST_SUCCESS = "📢 <b>Broadcast sent successfully!</b>\\n👥 Delivered to {} users\\n❌ Failed for {} users"
    EXEC_SUCCESS = "✅ <b>Command executed successfully!</b>"
    
    # Queue Messages  
    QUEUE_EMPTY = "📋 <b>Queue is empty!</b>\\n✨ Ready to process new compressions."
    ADDED_TO_QUEUE = "📝 <b>Added to compression queue!</b>\\n🔢 Position: {}\\n⏱️ Estimated wait time: {} minutes"
    
    # Other Messages
    FF_MPEG_RO_BOT_STOR_AGE_ALREADY_EXISTS = "⚠️ <b>Already one process running!</b>\\n\\nCheck status with /queue"
    SAVED_RECVD_DOC_FILE = "✅ <b>Downloaded Successfully!</b>"
    
    # Rate Limit Messages
    RATE_LIMIT_EXCEEDED = "🚫 <b>Rate limit exceeded!</b>\\n⏰ Please wait {} seconds before sending another request."
    FLOOD_BAN_MESSAGE = "🚫 <b>You have been temporarily banned for flooding!</b>\\n⏰ Ban duration: {} minutes\\n💡 Please respect the bot's limits."
    
    # Settings Messages
    SETTINGS_MENU = (
        "⚙️ <b>User Settings</b>\\n\\n"
        "🎨 <b>Default Quality:</b> {}\\n"
        "📱 <b>Output Format:</b> {}\\n"
        "🖼️ <b>Custom Thumbnail:</b> {}\\n"
        "📊 <b>Progress Updates:</b> {}\\n"
        "🔔 <b>Notifications:</b> {}\\n\\n"
        "💡 Use the buttons below to change settings"
    )
print("Created main module and localization files")
