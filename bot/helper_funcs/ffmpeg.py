#!/usr/bin/env python3

import logging
import asyncio
import os
import time
import re  # ✅ FIXED: Added missing import
import json
import subprocess
import math
from typing import Optional, Dict, Any

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.helper_funcs.display_progress import TimeFormatter
from bot.localisation import Localisation
from bot import (
    FINISHED_PROGRESS_STR,
    UN_FINISHED_PROGRESS_STR,
    DOWNLOAD_LOCATION
)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

LOGGER = logging.getLogger(__name__)

# Enhanced quality presets for button system compatibility
QUALITY_PRESETS = {
    '1080p': {'resolution': '1920x1080', 'crf': 18, 'preset': 'slow'},
    '1080p_hevc': {'resolution': '1920x1080', 'crf': 20, 'preset': 'medium', 'codec': 'libx265'},
    '720p': {'resolution': '1280x720', 'crf': 20, 'preset': 'medium'},
    '720p_hevc': {'resolution': '1280x720', 'crf': 22, 'preset': 'medium', 'codec': 'libx265'},
    '480p': {'resolution': '854x480', 'crf': 23, 'preset': 'fast'},
    '480p_hevc': {'resolution': '854x480', 'crf': 25, 'preset': 'fast', 'codec': 'libx265'},
    'custom': {'crf': 23, 'preset': 'medium'}
}

async def convert_video(video_file, output_directory, total_time, bot, message, target_percentage, isAuto=False, bug=None):
    """Enhanced video conversion with button system support and FIXED progress tracking"""
    try:
        # Generate output filename
        out_put_file_name = os.path.join(output_directory, f"{int(time.time())}.mp4")
        progress = os.path.join(output_directory, "progress.txt")
        
        with open(progress, 'w') as f:
            pass

        # Default FFmpeg command
        file_genertor_command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "quiet",
            "-progress", progress,
            "-i", video_file
        ]

        # ✅ FIXED: Check if this is button-based system call
        custom_settings_used = False
        
        if hasattr(message, 'from_user') and hasattr(message.from_user, 'id'):
            # Try to get custom settings from USER_SESSIONS
            try:
                from bot.plugins.incoming_message_fn import USER_SESSIONS
                user_id = message.from_user.id
                
                if user_id in USER_SESSIONS:
                    session = USER_SESSIONS[user_id]
                    LOGGER.info(f"Using button system settings for user {user_id}: {session.quality}")
                    
                    # Use custom settings from button system
                    file_genertor_command.extend([
                        "-c:v", session.video_codec,
                        "-preset", session.preset,
                        "-crf", str(session.crf),
                        "-pix_fmt", session.pixel_format
                    ])
                    
                    # Add resolution if specified
                    if session.resolution and session.resolution.lower() != "original":
                        file_genertor_command.extend(["-s", session.resolution])
                    
                    # Add audio settings
                    if session.audio_codec == "copy":
                        file_genertor_command.extend(["-c:a", "copy"])
                    else:
                        file_genertor_command.extend([
                            "-c:a", session.audio_codec,
                            "-b:a", session.audio_bitrate
                        ])
                    
                    # Add optimization flags
                    file_genertor_command.extend([
                        "-movflags", "+faststart",
                        "-tune", "film"
                    ])
                    
                    target_percentage = f"{session.quality}_CRF{session.crf}"
                    custom_settings_used = True
                    
                else:
                    raise Exception("No session found")
                    
            except Exception as e:
                LOGGER.info(f"No custom settings found, using legacy mode: {e}")
                custom_settings_used = False
        
        # If no custom settings, use legacy system (from working code)
        if not custom_settings_used:
            LOGGER.info("Using legacy compression mode")
            file_genertor_command.extend([
                "-c:v", "libx264",  # ✅ FIXED: was "h264"
                "-preset", "ultrafast",
                "-tune", "film",
                "-c:a", "copy"
            ])
            
            # Handle percentage-based compression (legacy mode)
            if not isAuto and isinstance(target_percentage, (int, float)):
                try:
                    filesize = os.stat(video_file).st_size
                    calculated_percentage = 100 - target_percentage
                    target_size = (calculated_percentage / 100) * filesize
                    target_bitrate = int(math.floor(target_size * 8 / total_time))
                    
                    if target_bitrate // 1000000 >= 1:
                        bitrate = str(target_bitrate//1000000) + "M"
                    elif target_bitrate // 1000 > 1:
                        bitrate = str(target_bitrate//1000) + "k"
                    else:
                        bitrate = "500k"  # Minimum bitrate
                    
                    # Insert bitrate control before output file
                    extra = ["-b:v", bitrate, "-bufsize", bitrate]
                    for elem in reversed(extra):
                        file_genertor_command.insert(10, elem)
                        
                    LOGGER.info(f"Using legacy bitrate mode: {bitrate}")
                    
                except Exception as e:
                    LOGGER.error(f"Error in legacy bitrate calculation: {e}")
                    # Continue with default settings
            else:
                target_percentage = 'auto'
        
        # Add output file
        file_genertor_command.append(out_put_file_name)
        
        LOGGER.info(f"FFmpeg command: {' '.join(file_genertor_command)}")
        
        # Start compression
        COMPRESSION_START_TIME = time.time()
        
        process = await asyncio.create_subprocess_exec(
            *file_genertor_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        LOGGER.info(f"Compression process started: {process.pid}")
        
        # Update status file (from working code)
        status = os.path.join(output_directory, "status.json")
        try:
            with open(status, 'r+') as f:
                statusMsg = json.load(f)
        except:
            statusMsg = {}
        
        statusMsg['pid'] = process.pid
        statusMsg['message'] = getattr(message, 'id', getattr(message, 'message_id', 0))
        
        with open(status, 'w') as f:
            json.dump(statusMsg, f, indent=2)
        
        # ✅ FIXED: Monitor progress with proper regex and progress bar
        isDone = False
        
        while process.returncode is None:  # ✅ FIXED: Correct condition
            await asyncio.sleep(3)
            
            try:
                if not os.path.exists(progress):
                    continue
                    
                # ✅ FIXED: Proper file reading with progress path
                with open(progress, 'r') as file:
                    text = file.read()
                
                # ✅ FIXED: Proper regex patterns (from working code)
                frame = re.findall(r"frame=(\d+)", text)
                time_in_us = re.findall(r"out_time_ms=(\d+)", text)
                progress_match = re.findall(r"progress=(\w+)", text)
                speed = re.findall(r"speed=([\d.]+)", text)
                
                # Handle completion
                if len(progress_match):
                    if progress_match[-1] == "end":
                        LOGGER.info("Compression completed")
                        isDone = True
                        break
                
                # Calculate progress
                if len(time_in_us) and total_time > 0:
                    elapsed_time = int(time_in_us[-1]) / 1000000
                    percentage = math.floor(elapsed_time * 100 / total_time) if total_time > 0 else 0
                    percentage = min(percentage, 100)  # Cap at 100%
                    
                    # Calculate ETA
                    try:
                        if len(speed) and float(speed[-1]) > 0:
                            difference = math.floor((total_time - elapsed_time) / float(speed[-1]))
                        else:
                            difference = 0
                    except:
                        difference = 0
                    
                    ETA = "-"
                    if difference > 0:
                        ETA = TimeFormatter(difference * 1000)
                    
                    execution_time = TimeFormatter((time.time() - COMPRESSION_START_TIME) * 1000)
                    
                    # ✅ FIXED: Proper progress bar creation (from working code)
                    progress_str = "📊 **Progress:** {0}%\n[{1}{2}]".format(
                        round(percentage, 2),
                        ''.join([FINISHED_PROGRESS_STR for i in range(math.floor(percentage / 10))]),
                        ''.join([UN_FINISHED_PROGRESS_STR for i in range(10 - math.floor(percentage / 10))])
                    )
                    
                    # Enhanced stats display (compatible with both systems)
                    if custom_settings_used:
                        stats = (
                            f'🎬 **Compressing** {target_percentage}\n\n'
                            f'⏰ **ETA:** {ETA}\n'
                            f'⏱️ **Elapsed:** {execution_time}\n\n'
                            f'{progress_str}'
                        )
                    else:
                        # Legacy stats format
                        stats = (
                            f'📦 **Compressing** {target_percentage}%\n\n'
                            f'⏰ **ETA:** {ETA}\n\n'
                            f'{progress_str}\n'
                        )
                    
                    try:
                        await message.edit_text(
                            text=stats,
                            reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton('❌ Cancel', callback_data='cancel_compression')
                            ]])
                        )
                    except Exception as edit_error:
                        LOGGER.warning(f"Could not edit progress message: {edit_error}")
                    
                    # Update log message if provided
                    if bug:
                        try:
                            await bug.edit_text(text=stats)
                        except Exception as bug_error:
                            LOGGER.warning(f"Could not edit log message: {bug_error}")
                
            except Exception as e:
                LOGGER.error(f"Progress monitoring error: {e}")
                continue
        
        # Wait for process completion
        stdout, stderr = await process.communicate()
        
        # ✅ FIXED: Better output handling (from working code)
        e_response = stderr.decode().strip() if stderr else ""
        t_response = stdout.decode().strip() if stdout else ""
        
        LOGGER.info(f"FFmpeg stdout: {t_response}")
        if e_response:
            LOGGER.error(f"FFmpeg stderr: {e_response}")
        
        # Clean up progress files (from working code)
        try:
            if os.path.exists(progress):
                os.remove(progress)
            if os.path.exists(status):
                os.remove(status)
        except Exception as cleanup_error:
            LOGGER.warning(f"Cleanup error: {cleanup_error}")
        
        # Check result
        if os.path.exists(out_put_file_name) and os.path.getsize(out_put_file_name) > 0:
            LOGGER.info(f"Compression successful: {out_put_file_name}")
            return out_put_file_name
        else:
            LOGGER.error("Output file not created or empty")
            return None
            
    except Exception as e:
        LOGGER.error(f"Video conversion error: {e}")
        return None

async def media_info(saved_file_path):
    """Enhanced media info with better async handling (from working code)"""
    try:
        process = await asyncio.create_subprocess_exec(
            'ffmpeg', '-hide_banner', '-i', saved_file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        output = stderr.decode().strip() if stderr else ""  # ffmpeg prints info to stderr
        
        # ✅ FIXED: Better regex patterns (from working code)
        duration = re.search(r"Duration:\s*(\d*):(\d*):(\d+\.?\d*)[\s\w*$]", output)
        bitrates = re.search(r"bitrate:\s*(\d+)[\s\w*$]", output)
        
        if duration is not None:
            hours = int(duration.group(1))
            minutes = int(duration.group(2))
            seconds = math.floor(float(duration.group(3)))
            total_seconds = (hours * 60 * 60) + (minutes * 60) + seconds
        else:
            total_seconds = None
        
        if bitrates is not None:
            bitrate = bitrates.group(1)
        else:
            bitrate = None
        
        return total_seconds, bitrate
        
    except Exception as e:
        LOGGER.error(f"Error getting media info: {e}")
        return None, None

async def take_screen_shot(video_file, output_directory, ttl):
    """Enhanced screenshot with better quality and error handling (from working code)"""
    try:
        out_put_file_name = os.path.join(
            output_directory,
            f"{int(time.time())}.jpg"
        )
        
        if video_file.upper().endswith(("MKV", "MP4", "WEBM", "AVI", "MOV", "FLV", "WMV")):
            file_genertor_command = [
                "ffmpeg",
                "-y",  # Overwrite output
                "-ss", str(ttl),
                "-i", video_file,
                "-vframes", "1",
                "-q:v", "2",  # High quality
                out_put_file_name
            ]
            
            process = await asyncio.create_subprocess_exec(
                *file_genertor_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            e_response = stderr.decode().strip() if stderr else ""
            t_response = stdout.decode().strip() if stdout else ""
            
            if e_response:
                LOGGER.warning(f"Thumbnail generation warning: {e_response}")
            
            if os.path.exists(out_put_file_name) and os.path.getsize(out_put_file_name) > 0:
                return out_put_file_name
            else:
                return None
        else:
            return None
            
    except Exception as e:
        LOGGER.error(f"Error generating thumbnail: {e}")
        return None

# Additional helper functions for button system compatibility

def get_quality_preset(quality_name: str) -> Dict[str, Any]:
    """Get quality preset configuration"""
    return QUALITY_PRESETS.get(quality_name, QUALITY_PRESETS['custom'])

async def convert_video_with_custom_settings(video_file, output_directory, total_time, bot, message, session, log_message=None):
    """Bridge function for custom settings compatibility"""
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

# Enhanced detailed media info functions (from ffmpeg-1.py)

async def get_media_info_detailed(file_path: str) -> Dict[str, Any]:
    """Get detailed media information using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', file_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            info = json.loads(stdout.decode())
            return parse_media_info(info)
        else:
            LOGGER.error(f"FFprobe error: {stderr.decode()}")
            return {}
        
    except Exception as e:
        LOGGER.error(f"Error getting detailed media info: {e}")
        return {}

def parse_media_info(info: Dict[str, Any]) -> Dict[str, Any]:
    """Parse ffprobe output into useful information"""
    try:
        format_info = info.get('format', {})
        streams = info.get('streams', [])
        
        video_stream = next((s for s in streams if s['codec_type'] == 'video'), None)
        audio_stream = next((s for s in streams if s['codec_type'] == 'audio'), None)
        
        duration = float(format_info.get('duration', 0))
        bitrate = int(format_info.get('bit_rate', 0))
        size = int(format_info.get('size', 0))
        
        result = {
            'duration': duration,
            'bitrate': bitrate,
            'size': size,
            'format': format_info.get('format_name', ''),
            'video': {},
            'audio': {}
        }
        
        if video_stream:
            result['video'] = {
                'codec': video_stream.get('codec_name', ''),
                'width': int(video_stream.get('width', 0)),
                'height': int(video_stream.get('height', 0)),
                'fps': eval(video_stream.get('r_frame_rate', '0/1')) if video_stream.get('r_frame_rate') else 0,
                'bitrate': int(video_stream.get('bit_rate', 0)) if video_stream.get('bit_rate') else 0
            }
        
        if audio_stream:
            result['audio'] = {
                'codec': audio_stream.get('codec_name', ''),
                'bitrate': int(audio_stream.get('bit_rate', 0)) if audio_stream.get('bit_rate') else 0,
                'sample_rate': int(audio_stream.get('sample_rate', 0)) if audio_stream.get('sample_rate') else 0,
                'channels': int(audio_stream.get('channels', 0)) if audio_stream.get('channels') else 0
            }
        
        return result
        
    except Exception as e:
        LOGGER.error(f"Error parsing media info: {e}")
        return {}

async def check_ffmpeg_availability() -> bool:
    """Check if ffmpeg and ffprobe are available"""
    try:
        # Check ffmpeg
        process = await asyncio.create_subprocess_exec(
            'ffmpeg', '-version',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        
        if process.returncode != 0:
            LOGGER.error("FFmpeg not found or not working")
            return False
        
        # Check ffprobe
        process = await asyncio.create_subprocess_exec(
            'ffprobe', '-version',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        
        if process.returncode != 0:
            LOGGER.error("FFprobe not found or not working")
            return False
        
        return True
        
    except Exception as e:
        LOGGER.error(f"Error checking ffmpeg availability: {e}")
        return False

# Export main functions
__all__ = [
    'convert_video',
    'media_info',
    'take_screen_shot',
    'convert_video_with_custom_settings',
    'get_quality_preset',
    'get_media_info_detailed',
    'parse_media_info',
    'check_ffmpeg_availability'
]
