# 9. bot/helper_funcs/display_progress.py - Enhanced progress display

import math
import os
import time
import asyncio
import logging
from typing import Optional, Callable, Any
from pyrogram.types import Message

LOGGER = logging.getLogger(__name__)

def humanbytes(size: int) -> str:
    """Convert bytes to human readable format"""
    if not size:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size / p, 2)
    return f"{s} {size_names[i]}"

def TimeFormatter(milliseconds: int) -> str:
    """Format milliseconds to human readable time"""
    if milliseconds < 0:
        return "0s"
    
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def calculate_eta(current: int, total: int, start_time: float) -> str:
    """Calculate estimated time of arrival"""
    if current == 0 or total == 0:
        return "Calculating..."
    
    try:
        elapsed_time = time.time() - start_time
        if elapsed_time <= 0:
            return "Calculating..."
            
        rate = current / elapsed_time
        if rate <= 0:
            return "Calculating..."
            
        remaining_bytes = total - current
        eta_seconds = remaining_bytes / rate
        return TimeFormatter(int(eta_seconds * 1000))
    except:
        return "Calculating..."

def create_progress_bar(percentage: float, length: int = 20) -> str:
    """Create a visual progress bar"""
    if percentage < 0:
        percentage = 0
    elif percentage > 100:
        percentage = 100
        
    filled_length = int(length * percentage // 100)
    bar = '█' * filled_length + '░' * (length - filled_length)
    return f"[{bar}] {percentage:.1f}%"

async def progress_for_pyrogram(
    current: int,
    total: int,
    ud_type: str,
    message: Message,
    start_time: float,
    bot=None
) -> None:
    """Enhanced progress callback for Pyrogram"""
    try:
        now = time.time()
        diff = now - start_time
        
        if diff < 2:  # Update every 2 seconds minimum
            return
            
        if round(diff % 5.00) == 0 or current == total:
            percentage = current * 100 / total if total > 0 else 0
            speed = current / diff if diff > 0 else 0
            eta = calculate_eta(current, total, start_time)
            
            # Progress bar
            progress_bar = create_progress_bar(percentage)
            
            # Format file sizes
            current_size = humanbytes(current)
            total_size = humanbytes(total)
            speed_str = f"{humanbytes(int(speed))}/s"
            
            # Enhanced progress message
            progress_text = (
                f"🔄 **{ud_type}**\\n\\n"
                f"{progress_bar}\\n\\n"
                f"📊 **Progress:** {percentage:.1f}%\\n"
                f"📦 **Size:** {current_size} / {total_size}\\n"
                f"🚀 **Speed:** {speed_str}\\n"
                f"⏱️ **ETA:** {eta}\\n"
                f"⏰ **Elapsed:** {TimeFormatter(int(diff * 1000))}"
            )
            
            try:
                await message.edit_text(progress_text)
            except Exception as e:
                LOGGER.error(f"Error updating progress: {e}")
                
    except Exception as e:
        LOGGER.error(f"Progress callback error: {e}")

class ProgressTracker:
    """Advanced progress tracking class"""
    
    def __init__(self, message: Message, operation: str):
        self.message = message
        self.operation = operation
        self.start_time = time.time()
        self.last_update = 0
        self.update_interval = 2  # seconds
    
    async def update(self, current: int, total: int, **kwargs):
        """Update progress with additional information"""
        now = time.time()
        
        if now - self.last_update < self.update_interval:
            return
            
        try:
            percentage = (current / total) * 100 if total > 0 else 0
            elapsed = now - self.start_time
            
            # Calculate speed and ETA
            if elapsed > 0:
                speed = current / elapsed
                eta_seconds = (total - current) / speed if speed > 0 else 0
                eta = TimeFormatter(int(eta_seconds * 1000))
                speed_str = f"{humanbytes(int(speed))}/s"
            else:
                eta = "Calculating..."
                speed_str = "0 B/s"
            
            # Additional info from kwargs
            extra_info = ""
            if 'quality' in kwargs:
                extra_info += f"🎯 **Quality:** {kwargs['quality']}%\\n"
            if 'format' in kwargs:
                extra_info += f"📄 **Format:** {kwargs['format'].upper()}\\n"
            if 'codec' in kwargs:
                extra_info += f"🔧 **Codec:** {kwargs['codec'].upper()}\\n"
            
            progress_text = (
                f"⚡ **{self.operation}**\\n\\n"
                f"{create_progress_bar(percentage, 25)}\\n\\n"
                f"📈 **Progress:** {percentage:.1f}%\\n"
                f"📦 **Size:** {humanbytes(current)} / {humanbytes(total)}\\n"
                f"🚀 **Speed:** {speed_str}\\n"
                f"⏳ **ETA:** {eta}\\n"
                f"⏰ **Elapsed:** {TimeFormatter(int(elapsed * 1000))}\\n"
                f"{extra_info}"
                f"\\n💡 *Enhanced VideoCompress Bot v2.0*"
            )
            
            await self.message.edit_text(progress_text)
            self.last_update = now
            
        except Exception as e:
            LOGGER.error(f"Progress tracker error: {e}")
    
    async def complete(self, final_message: str = None):
        """Mark progress as complete"""
        try:
            elapsed = time.time() - self.start_time
            
            if final_message:
                completion_text = (
                    f"✅ **{self.operation} Complete!**\\n\\n"
                    f"{final_message}\\n\\n"
                    f"⏰ **Total Time:** {TimeFormatter(int(elapsed * 1000))}\\n"
                    f"💎 *Enhanced VideoCompress Bot v2.0*"
                )
            else:
                completion_text = (
                    f"✅ **{self.operation} completed successfully!**\\n"
                    f"⏰ **Total Time:** {TimeFormatter(int(elapsed * 1000))}"
                )
            
            await self.message.edit_text(completion_text)
            
        except Exception as e:
            LOGGER.error(f"Progress completion error: {e}")
    
    async def error(self, error_message: str):
        """Mark progress as failed"""
        try:
            elapsed = time.time() - self.start_time
            
            error_text = (
                f"❌ **{self.operation} Failed**\\n\\n"
                f"🔍 **Error:** {error_message}\\n"
                f"⏰ **Duration:** {TimeFormatter(int(elapsed * 1000))}\\n\\n"
                f"💡 *Please try again or contact support*"
            )
            
            await self.message.edit_text(error_text)
            
        except Exception as e:
            LOGGER.error(f"Progress error display failed: {e}")

# Enhanced progress callback factory
def create_progress_callback(
    message: Message, 
    operation: str,
    update_interval: float = 2.0
) -> Callable:
    """Create a customized progress callback"""
    
    start_time = time.time()
    last_update = 0
    
    async def progress_callback(current: int, total: int, **kwargs):
        nonlocal last_update
        
        now = time.time()
        if now - last_update < update_interval:
            return
            
        tracker = ProgressTracker(message, operation)
        tracker.start_time = start_time
        await tracker.update(current, total, **kwargs)
        
        last_update = now
    
    return progress_callback
