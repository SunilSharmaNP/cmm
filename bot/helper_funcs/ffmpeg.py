# 11. bot/helper_funcs/ffmpeg.py - Enhanced FFmpeg handler

import asyncio
import os
import time
import re
import json
import subprocess
import math
import logging
from typing import Optional, Dict, Any, Tuple
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.helper_funcs.display_progress import TimeFormatter
from bot.localisation import Localisation
from bot import (
    FINISHED_PROGRESS_STR,
    UN_FINISHED_PROGRESS_STR,
    DOWNLOAD_LOCATION
)

LOGGER = logging.getLogger(__name__)

async def convert_video(video_file, output_directory, total_time, bot, message, target_percentage, isAuto=False, bug=None):
    """Enhanced video conversion with better error handling"""
    try:
        # https://stackoverflow.com/a/13891070/4723940
        out_put_file_name = output_directory + "/" + str(round(time.time())) + ".mp4"
        progress = output_directory + "/" + "progress.txt"
        
        with open(progress, 'w') as f:
            pass

        file_genertor_command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "quiet",
            "-progress",
            progress,
            "-i",
            video_file,
            "-c:v",   
            "libx264",
            "-preset",   
            "ultrafast",
            "-tune",
            "film",
            "-c:a",
            "copy",
            out_put_file_name
        ]
        
        if not isAuto:
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
                    
                extra = ["-b:v", bitrate, "-bufsize", bitrate]
                for elem in reversed(extra):
                    file_genertor_command.insert(10, elem)
            except Exception as e:
                LOGGER.error(f"Error calculating bitrate: {e}")
                # Continue with default settings
        else:
            target_percentage = 'auto'
        
        COMPRESSION_START_TIME = time.time()
        
        process = await asyncio.create_subprocess_exec(
            *file_genertor_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        LOGGER.info("ffmpeg_process: " + str(process.pid))
        
        status = output_directory + "/status.json"
        try:
            with open(status, 'r+') as f:
                statusMsg = json.load(f)
        except:
            statusMsg = {}
            
        statusMsg['pid'] = process.pid
        statusMsg['message'] = message.id
        
        with open(status, 'w') as f:
            json.dump(statusMsg, f, indent=2)

        isDone = False
        while process.returncode is None:
            await asyncio.sleep(3)
            
            try:
                with open(progress, 'r') as file:
                    text = file.read()
                    
                frame = re.findall("frame=(\\d+)", text)
                time_in_us = re.findall("out_time_ms=(\\d+)", text)
                progress_match = re.findall("progress=(\\w+)", text)
                speed = re.findall("speed=([\\d.]+)", text)
                
                if len(frame):
                    frame = int(frame[-1])
                else:
                    frame = 1
                    
                if len(speed):
                    speed = speed[-1]
                else:
                    speed = "1"
                    
                if len(time_in_us):
                    time_in_us = time_in_us[-1]
                else:
                    time_in_us = "1"
                    
                if len(progress_match):
                    if progress_match[-1] == "end":
                        LOGGER.info(progress_match[-1])
                        isDone = True
                        break
                
                execution_time = TimeFormatter((time.time() - COMPRESSION_START_TIME) * 1000)
                elapsed_time = int(time_in_us) / 1000000
                
                try:
                    difference = math.floor((total_time - elapsed_time) / float(speed))
                except:
                    difference = 0
                
                ETA = "-"
                if difference > 0:
                    ETA = TimeFormatter(difference * 1000)

                percentage = math.floor(elapsed_time * 100 / total_time) if total_time > 0 else 0
                percentage = min(percentage, 100)  # Cap at 100%
                
                progress_str = "📊 **Progress:** {0}%\\n[{1}{2}]".format(
                    round(percentage, 2),
                    ''.join([FINISHED_PROGRESS_STR for i in range(math.floor(percentage / 10))]),
                    ''.join([UN_FINISHED_PROGRESS_STR for i in range(10 - math.floor(percentage / 10))])
                )
                
                stats = f'📦️ **Compressing** {target_percentage}%\\n\\n' \
                       f'⏰️ **ETA:** {ETA}\\n\\n' \
                       f'{progress_str}\\n'
                
                try:
                    await message.edit_text(
                        text=stats,
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton('❌ Cancel ❌', callback_data='cancel_compression')
                        ]])
                    )
                except:
                    pass
                
                try:
                    if bug:
                        await bug.edit_text(text=stats)
                except:
                    pass
                    
            except Exception as e:
                LOGGER.error(f"Progress monitoring error: {e}")
                continue

        # Wait for the subprocess to finish
        stdout, stderr = await process.communicate()
        
        e_response = stderr.decode().strip() if stderr else ""
        t_response = stdout.decode().strip() if stdout else ""
        
        LOGGER.info(f"FFmpeg stdout: {t_response}")
        if e_response:
            LOGGER.error(f"FFmpeg stderr: {e_response}")
        
        # Clean up progress files
        try:
            if os.path.exists(progress):
                os.remove(progress)
            if os.path.exists(status):
                os.remove(status)
        except:
            pass
        
        if os.path.lexists(out_put_file_name):
            return out_put_file_name
        else:
            return None
            
    except Exception as e:
        LOGGER.error(f"Video conversion error: {e}")
        return None

async def media_info(saved_file_path):
    """Get media information using ffmpeg"""
    try:
        process = await asyncio.create_subprocess_exec(
            'ffmpeg',   
            "-hide_banner",   
            '-i',   
            saved_file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        output = stderr.decode().strip() if stderr else ""
        
        duration = re.search("Duration:\\s*(\\d*):(\\d*):(\\d+\\.?\\d*)[\\s\\w*$]", output)
        bitrates = re.search("bitrate:\\s*(\\d+)[\\s\\w*$]", output)

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
    """Generate video thumbnail"""
    try:
        out_put_file_name = os.path.join(
            output_directory,
            str(time.time()) + ".jpg"
        )
        
        if video_file.upper().endswith(("MKV", "MP4", "WEBM", "AVI", "MOV", "FLV", "WMV")):
            file_genertor_command = [
                "ffmpeg",
                "-y",
                "-ss",
                str(ttl),
                "-i",
                video_file,
                "-vframes",
                "1",
                "-q:v",
                "2",
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
            
            if os.path.lexists(out_put_file_name):
                return out_put_file_name
            else:
                return None
        else:
            return None
            
    except Exception as e:
        LOGGER.error(f"Error generating thumbnail: {e}")
        return None

# Enhanced media info function
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

# Check if ffmpeg is available
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
        
