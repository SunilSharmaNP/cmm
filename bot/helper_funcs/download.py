

import asyncio
import logging
import math
import os
import time
import aiofiles
from datetime import datetime
from typing import Optional, Callable, Any
from pathlib import Path

from pyrogram import Client
from pyrogram.types import Message

from bot import DOWNLOAD_LOCATION
from bot.helper_funcs.display_progress import (
    progress_for_pyrogram,
    ProgressTracker,
    humanbytes,
    TimeFormatter
)
from bot.helper_funcs.utils import (
    FileManager,
    ValidationUtils,
    SystemUtils
)

LOGGER = logging.getLogger(__name__)

class EnhancedDownloader:
    """Enhanced file downloader with advanced features"""
    
    def __init__(self):
        self.active_downloads = {}
        self.download_stats = {
            'total_downloads': 0,
            'total_size': 0,
            'failed_downloads': 0
        }
    
    async def download_media(
        self, 
        client: Client, 
        message: Message,
        custom_path: Optional[str] = None,
        progress_callback: Optional[Callable] = None
    ) -> Optional[str]:
        """
        Enhanced media download with comprehensive error handling
        """
        user_id = message.from_user.id
        
        try:
            # Check if user has active download
            if user_id in self.active_downloads:
                return None
            
            # Mark user as having active download
            self.active_downloads[user_id] = True
            
            # Validate message has media
            if not message.reply_to_message:
                await message.reply_text(
                    "❌ **No media found!**\n\n"
                    "Please reply to a video, photo, document, or audio file."
                )
                return None
            
            replied_message = message.reply_to_message
            media = (replied_message.video or replied_message.document or 
                    replied_message.photo or replied_message.audio)
            
            if not media:
                await message.reply_text(
                    "❌ **Unsupported media type!**\n\n"
                    "Please reply to a video, photo, document, or audio file."
                )
                return None
            
            # Check file size
            file_size = getattr(media, 'file_size', 0)
            if not ValidationUtils.validate_file_size(file_size, 2 * 1024 * 1024 * 1024):  # 2GB limit
                await message.reply_text(
                    f"❌ **File too large!**\n\n"
                    f"📏 **Size:** {humanbytes(file_size)}\n"
                    f"🔢 **Limit:** 2GB\n\n"
                    f"💡 *Please use a smaller file*"
                )
                return None
            
            # Prepare download directory
            download_dir = custom_path or DOWNLOAD_LOCATION
            os.makedirs(download_dir, exist_ok=True)
            
            # Generate unique filename
            file_name = getattr(media, 'file_name', None)
            if not file_name:
                file_extension = self._get_file_extension(media)
                file_name = f"{user_id}_{int(time.time())}{file_extension}"
            
            # Sanitize filename
            file_name = ValidationUtils.sanitize_filename(file_name)
            download_path = os.path.join(download_dir, file_name)
            
            # Send initial status
            status_message = await message.reply_text(
                f"📥 **Starting Download...**\n\n"
                f"📄 **File:** {file_name}\n"
                f"📏 **Size:** {humanbytes(file_size)}\n"
                f"⏰ **Started:** {datetime.now().strftime('%H:%M:%S')}\n\n"
                f"⏳ *Please wait while I download your file...*"
            )
            
            # Initialize progress tracker
            if not progress_callback:
                progress_callback = lambda current, total: asyncio.create_task(
                    self._update_progress(status_message, current, total, file_name)
                )
            
            # Start download
            start_time = time.time()
            
            try:
                downloaded_file = await client.download_media(
                    message=replied_message,
                    file_name=download_path,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        "Downloading",
                        status_message,
                        start_time
                    )
                )
                
                if not downloaded_file or not os.path.exists(downloaded_file):
                    raise Exception("Download failed - file not created")
                
                # Verify download
                downloaded_size = os.path.getsize(downloaded_file)
                if downloaded_size != file_size and file_size > 0:
                    LOGGER.warning(f"Size mismatch: expected {file_size}, got {downloaded_size}")
                
                # Calculate download time
                download_time = time.time() - start_time
                download_speed = downloaded_size / download_time if download_time > 0 else 0
                
                # Update statistics
                self.download_stats['total_downloads'] += 1
                self.download_stats['total_size'] += downloaded_size
                
                # Final success message
                await status_message.edit_text(
                    f"✅ **Download Completed!**\n\n"
                    f"📄 **File:** {file_name}\n"
                    f"📏 **Size:** {humanbytes(downloaded_size)}\n"
                    f"⏱️ **Time:** {TimeFormatter(int(download_time * 1000))}\n"
                    f"🚀 **Speed:** {humanbytes(int(download_speed))}/s\n"
                    f"📁 **Path:** `{downloaded_file}`\n\n"
                    f"🎉 *Ready for processing!*"
                )
                
                LOGGER.info(f"Successfully downloaded {file_name} for user {user_id}")
                return downloaded_file
                
            except Exception as download_error:
                LOGGER.error(f"Download failed for user {user_id}: {download_error}")
                
                # Update failed download stats
                self.download_stats['failed_downloads'] += 1
                
                await status_message.edit_text(
                    f"❌ **Download Failed!**\n\n"
                    f"📄 **File:** {file_name}\n"
                    f"🔍 **Error:** {str(download_error)[:100]}...\n"
                    f"⏰ **Time:** {TimeFormatter(int((time.time() - start_time) * 1000))}\n\n"
                    f"💡 *Please try again or contact support*"
                )
                
                # Clean up partial download
                if os.path.exists(download_path):
                    await FileManager.safe_remove(download_path)
                
                return None
                
        except Exception as e:
            LOGGER.error(f"Download handler error for user {user_id}: {e}")
            self.download_stats['failed_downloads'] += 1
            return None
            
        finally:
            # Remove user from active downloads
            if user_id in self.active_downloads:
                del self.active_downloads[user_id]
    
    async def _update_progress(self, message: Message, current: int, total: int, filename: str):
        """Update download progress"""
        try:
            if total == 0:
                return
                
            percentage = (current / total) * 100
            
            progress_text = (
                f"📥 **Downloading:** {filename}\n\n"
                f"📊 **Progress:** {percentage:.1f}%\n"
                f"📦 **Size:** {humanbytes(current)} / {humanbytes(total)}\n\n"
                f"⏳ *Please wait...*"
            )
            
            await message.edit_text(progress_text)
            
        except Exception as e:
            LOGGER.error(f"Progress update error: {e}")
    
    def _get_file_extension(self, media) -> str:
        """Get appropriate file extension based on media type"""
        if hasattr(media, 'mime_type'):
            mime_type = media.mime_type
            if mime_type:
                if 'video' in mime_type:
                    return '.mp4'
                elif 'audio' in mime_type:
                    return '.mp3'
                elif 'image' in mime_type:
                    return '.jpg'
                elif 'application/pdf' in mime_type:
                    return '.pdf'
                elif 'application/zip' in mime_type:
                    return '.zip'
        
        # Default extensions based on media type
        if hasattr(media, 'duration'):  # Video or audio
            return '.mp4' if hasattr(media, 'width') else '.mp3'
        
        return '.file'  # Generic extension
    
    async def get_download_stats(self) -> dict:
        """Get download statistics"""
        return {
            'total_downloads': self.download_stats['total_downloads'],
            'total_size_formatted': humanbytes(self.download_stats['total_size']),
            'total_size_bytes': self.download_stats['total_size'],
            'failed_downloads': self.download_stats['failed_downloads'],
            'success_rate': (
                (self.download_stats['total_downloads'] - self.download_stats['failed_downloads']) / 
                max(self.download_stats['total_downloads'], 1)
            ) * 100,
            'active_downloads': len(self.active_downloads)
        }
    
    async def cancel_user_download(self, user_id: int) -> bool:
        """Cancel active download for user"""
        if user_id in self.active_downloads:
            del self.active_downloads[user_id]
            LOGGER.info(f"Cancelled download for user {user_id}")
            return True
        return False
    
    async def cleanup_old_downloads(self, max_age_hours: int = 24) -> int:
        """Clean up old downloaded files"""
        try:
            from bot.helper_funcs.utils import CleanupManager
            return await CleanupManager.cleanup_old_files(DOWNLOAD_LOCATION, max_age_hours)
        except Exception as e:
            LOGGER.error(f"Cleanup error: {e}")
            return 0

# Global downloader instance
downloader = EnhancedDownloader()

# Legacy function for backward compatibility
async def down_load_media_f(client: Client, message: Message) -> Optional[str]:
    """
    Legacy download function for backward compatibility
    """
    return await downloader.download_media(client, message)

# Enhanced download function with additional options
async def download_media_enhanced(
    client: Client,
    message: Message,
    custom_path: Optional[str] = None,
    show_progress: bool = True
) -> Optional[str]:
    """
    Enhanced download function with additional options
    """
    if show_progress:
        return await downloader.download_media(client, message, custom_path)
    else:
        # Simple download without progress updates
        try:
            if not message.reply_to_message:
                return None
            
            download_dir = custom_path or DOWNLOAD_LOCATION
            os.makedirs(download_dir, exist_ok=True)
            
            return await client.download_media(
                message=message.reply_to_message,
                file_name=download_dir
            )
        except Exception as e:
            LOGGER.error(f"Simple download failed: {e}")
            return None

# Batch download function
async def download_multiple_files(
    client: Client,
    messages: list,
    download_dir: Optional[str] = None
) -> list:
    """
    Download multiple files concurrently
    """
    download_tasks = []
    download_dir = download_dir or DOWNLOAD_LOCATION
    
    for message in messages:
        if message.reply_to_message:
            task = downloader.download_media(client, message, download_dir)
            download_tasks.append(task)
    
    results = await asyncio.gather(*download_tasks, return_exceptions=True)
    
    # Filter successful downloads
    successful_downloads = [
        result for result in results 
        if isinstance(result, str) and os.path.exists(result)
    ]
    
    return successful_downloads

# URL download function (placeholder for future enhancement)
async def download_from_url(
    url: str,
    download_dir: Optional[str] = None,
    filename: Optional[str] = None
) -> Optional[str]:
    """
    Download file from URL (placeholder for future implementation)
    """
    # This would be implemented for downloading from external URLs
    # For now, it's a placeholder
    LOGGER.info(f"URL download requested: {url}")
    return None
