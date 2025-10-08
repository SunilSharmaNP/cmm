# 16. bot/plugins/new_join_fn.py - Enhanced help handler

from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.localisation import Localisation

async def help_message_f(bot: Client, update: Message):
    """Enhanced help command handler"""
    try:
        help_keyboard = [
            [
                InlineKeyboardButton('🎬 Start Compressing', callback_data='start'),
                InlineKeyboardButton('📊 Bot Status', callback_data='status')
            ],
            [
                InlineKeyboardButton('⚙️ Settings', callback_data='settings'),
                InlineKeyboardButton('📋 Commands', callback_data='commands')
            ],
            [
                InlineKeyboardButton('🔗 Updates Channel', url='https://t.me/Discovery_Updates'),
                InlineKeyboardButton('💬 Support Group', url='https://t.me/linux_repo')
            ],
            [
                InlineKeyboardButton('📖 Documentation', url='https://github.com/enhanced/videocompress-bot/wiki'),
                InlineKeyboardButton('🐛 Report Bug', url='https://github.com/enhanced/videocompress-bot/issues')
            ]
        ]
        
        await update.reply_text(
            Localisation.HELP_MESSAGE,
            reply_markup=InlineKeyboardMarkup(help_keyboard),
            reply_to_message_id=update.id
        )
        
    except Exception as e:
        await update.reply_text(
            "❌ Error showing help. Please try again later.\\n\\n"
            "💬 If this persists, contact our support group: @linux_repo"
        )

async def about_message_f(bot: Client, update: Message):
    """About command handler"""
    try:
        about_text = (
            "🎬 **Enhanced VideoCompress Bot v2.0**\\n\\n"
            "🚀 **Advanced Features:**\\n"
            "• Multiple compression quality presets\\n"
            "• Support for various video formats\\n"
            "• Real-time progress tracking\\n"
            "• Queue management system\\n"
            "• Custom thumbnail support\\n"
            "• Advanced admin controls\\n"
            "• Database integration\\n"
            "• Rate limiting & spam protection\\n\\n"
            "🛠️ **Built with:**\\n"
            "• Python 3.8+\\n"
            "• Pyrogram 2.0\\n"
            "• FFmpeg\\n"
            "• MongoDB\\n\\n"
            "👥 **Original by:** @AbirHasan2005\\n"
            "⚡ **Enhanced by:** Research Team\\n\\n"
            "💡 **Open Source:** GPL-3.0 License\\n"
            "🔗 **Source Code:** Available on GitHub"
        )
        
        about_keyboard = [
            [
                InlineKeyboardButton('📖 Documentation', url='https://github.com/enhanced/videocompress-bot/wiki'),
                InlineKeyboardButton('⭐ Star on GitHub', url='https://github.com/enhanced/videocompress-bot')
            ],
            [
                InlineKeyboardButton('🔙 Back to Help', callback_data='help')
            ]
        ]
        
        await update.reply_text(
            about_text,
            reply_markup=InlineKeyboardMarkup(about_keyboard)
        )
        
    except Exception as e:
        await update.reply_text("❌ Error showing about information")

async def commands_list_f(bot: Client, update: Message):
    """List all available commands"""
    try:
        commands_text = (
            "📋 **Available Commands**\\n\\n"
            "**🔸 Public Commands:**\\n"
            "• `/start` - Start the bot\\n"
            "• `/help` - Show help information\\n"
            "• `/about` - About this bot\\n"
            "• `/compress [quality]` - Compress video\\n"
            "  - `/compress` - Auto quality\\n"
            "  - `/compress 50` - 50% compression\\n"
            "  - `/compress high` - High quality\\n"
            "  - `/compress medium` - Medium quality\\n"
            "  - `/compress low` - Low quality\\n\\n"
            "**🔸 Usage Examples:**\\n"
            "1. Send a video file to the bot\\n"
            "2. Reply to the video with `/compress`\\n"
            "3. Wait for the compression to complete\\n\\n"
            "**🔸 Supported Formats:**\\n"
            "• Input: MP4, MKV, AVI, MOV, WEBM, FLV, WMV\\n"
            "• Output: MP4, MKV, WEBM, AVI\\n\\n"
            "**🔸 File Size Limits:**\\n"
            "• Maximum: 2GB (Telegram limit)\\n"
            "• Recommended: Under 1GB for faster processing\\n\\n"
            "💡 **Tip:** Use quality presets for best results!"
        )
        
        commands_keyboard = [
            [
                InlineKeyboardButton('🎬 Try Compressing', callback_data='start'),
                InlineKeyboardButton('❓ Get Help', callback_data='help')
            ]
        ]
        
        await update.reply_text(
            commands_text,
            reply_markup=InlineKeyboardMarkup(commands_keyboard)
        )
        
    except Exception as e:
        await update.reply_text("❌ Error showing commands list")
