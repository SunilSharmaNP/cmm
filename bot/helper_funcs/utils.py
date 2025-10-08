# 10. bot/helper_funcs/utils.py - Enhanced utilities

import os
import shutil
import asyncio
import hashlib
import mimetypes
import logging
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import tempfile
import time
from datetime import datetime, timedelta

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import aiofiles
    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False

from bot import DOWNLOAD_LOCATION

LOGGER = logging.getLogger(__name__)

class FileManager:
    """Enhanced file management utilities"""
    
    @staticmethod
    async def safe_remove(file_path: str) -> bool:
        """Safely remove a file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                LOGGER.info(f"Removed file: {file_path}")
                return True
            return False
        except Exception as e:
            LOGGER.error(f"Error removing file {file_path}: {e}")
            return False
    
    @staticmethod
    async def safe_remove_dir(dir_path: str) -> bool:
        """Safely remove a directory and its contents"""
        try:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
                LOGGER.info(f"Removed directory: {dir_path}")
                return True
            return False
        except Exception as e:
            LOGGER.error(f"Error removing directory {dir_path}: {e}")
            return False
    
    @staticmethod
    async def get_file_hash(file_path: str, algorithm: str = 'md5') -> Optional[str]:
        """Calculate file hash"""
        try:
            hash_func = getattr(hashlib, algorithm)()
            
            if HAS_AIOFILES:
                async with aiofiles.open(file_path, 'rb') as f:
                    while chunk := await f.read(8192):
                        hash_func.update(chunk)
            else:
                with open(file_path, 'rb') as f:
                    while chunk := f.read(8192):
                        hash_func.update(chunk)
                        
            return hash_func.hexdigest()
            
        except Exception as e:
            LOGGER.error(f"Error calculating hash for {file_path}: {e}")
            return None
    
    @staticmethod
    def get_file_type(file_path: str) -> Tuple[str, str]:
        """Get file type and subtype"""
        try:
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type:
                main_type, sub_type = mime_type.split('/', 1)
                return main_type, sub_type
        except:
            pass
        return 'unknown', 'unknown'
    
    @staticmethod
    def is_video_file(file_path: str) -> bool:
        """Check if file is a video"""
        main_type, _ = FileManager.get_file_type(file_path)
        return main_type == 'video'
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except:
            return 0
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size to human readable"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
    
    @staticmethod
    async def create_temp_dir() -> str:
        """Create temporary directory"""
        try:
            temp_dir = tempfile.mkdtemp(prefix='videocompress_')
            return temp_dir
        except Exception as e:
            LOGGER.error(f"Error creating temp directory: {e}")
            return DOWNLOAD_LOCATION
    
    @staticmethod
    async def move_file(src: str, dst: str) -> bool:
        """Move file safely"""
        try:
            shutil.move(src, dst)
            return True
        except Exception as e:
            LOGGER.error(f"Error moving file {src} to {dst}: {e}")
            return False
    
    @staticmethod
    async def copy_file(src: str, dst: str) -> bool:
        """Copy file safely"""
        try:
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            LOGGER.error(f"Error copying file {src} to {dst}: {e}")
            return False

class SystemUtils:
    """System utility functions"""
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get system information"""
        try:
            if not HAS_PSUTIL:
                return {
                    'cpu_count': os.cpu_count(),
                    'cpu_percent': 0,
                    'memory_total': 0,
                    'memory_available': 0,
                    'memory_percent': 0,
                    'disk_total': 0,
                    'disk_free': 0,
                    'disk_percent': 0
                }
            
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_count = psutil.cpu_count()
            
            return {
                'cpu_count': cpu_count,
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_total': memory.total,
                'memory_available': memory.available,
                'memory_percent': memory.percent,
                'disk_total': disk.total,
                'disk_free': disk.free,
                'disk_percent': disk.percent
            }
        except Exception as e:
            LOGGER.error(f"Error getting system info: {e}")
            return {}
    
    @staticmethod
    def get_process_info(pid: int) -> Optional[Dict[str, Any]]:
        """Get process information"""
        try:
            if not HAS_PSUTIL:
                return None
                
            process = psutil.Process(pid)
            return {
                'pid': pid,
                'name': process.name(),
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'status': process.status(),
                'create_time': process.create_time()
            }
        except Exception as e:
            LOGGER.error(f"Error getting process info for PID {pid}: {e}")
            return None
    
    @staticmethod
    async def kill_process(pid: int) -> bool:
        """Kill process safely"""
        try:
            if not HAS_PSUTIL:
                return False
                
            process = psutil.Process(pid)
            process.terminate()
            
            # Wait for termination
            try:
                process.wait(timeout=5)
            except psutil.TimeoutExpired:
                process.kill()  # Force kill if doesn't terminate
                
            return True
            
        except Exception as e:
            LOGGER.error(f"Error killing process {pid}: {e}")
            return False

class ValidationUtils:
    """Input validation utilities"""
    
    @staticmethod
    def validate_compression_quality(quality: str) -> Tuple[bool, int]:
        """Validate compression quality input"""
        try:
            if quality.lower() in ['high', 'medium', 'low']:
                quality_map = {'high': 25, 'medium': 50, 'low': 75}
                return True, quality_map[quality.lower()]
            
            quality_int = int(quality)
            if 10 <= quality_int <= 90:
                return True, quality_int
            else:
                return False, 50
                
        except:
            return False, 50
    
    @staticmethod
    def validate_file_size(file_size: int, max_size: int) -> bool:
        """Validate file size against limit"""
        return file_size <= max_size
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
        """Validate file extension"""
        ext = os.path.splitext(filename)[1].lower().lstrip('.')
        return ext in [e.lower() for e in allowed_extensions]
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe usage"""
        # Remove or replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename

class CleanupManager:
    """Cleanup management utilities"""
    
    @staticmethod
    async def cleanup_old_files(directory: str, max_age_hours: int = 24) -> int:
        """Clean up old files in directory"""
        cleaned = 0
        try:
            if not os.path.exists(directory):
                return 0
                
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_time < cutoff_time:
                            os.remove(file_path)
                            cleaned += 1
                    except:
                        continue
                        
            LOGGER.info(f"Cleaned {cleaned} old files from {directory}")
            return cleaned
            
        except Exception as e:
            LOGGER.error(f"Error during cleanup: {e}")
            return cleaned
    
    @staticmethod
    async def cleanup_temp_files() -> int:
        """Clean up temporary files"""
        return await CleanupManager.cleanup_old_files(DOWNLOAD_LOCATION, 6)
    
    @staticmethod
    async def get_directory_size(directory: str) -> int:
        """Get total size of directory"""
        total_size = 0
        try:
            if not os.path.exists(directory):
                return 0
                
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except:
                        continue
        except Exception as e:
            LOGGER.error(f"Error calculating directory size: {e}")
        
        return total_size

# Legacy compatibility function
async def delete_downloads():
    """Legacy function for backward compatibility"""
    await CleanupManager.cleanup_temp_files()

# Additional utility functions
def format_duration(seconds: float) -> str:
    """Format duration in seconds to readable format"""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:.0f}m {secs:.0f}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:.0f}h {minutes:.0f}m {secs:.0f}s"

def bytes_to_mb(bytes_value: int) -> float:
    """Convert bytes to megabytes"""
    return bytes_value / (1024 * 1024)

def mb_to_bytes(mb_value: float) -> int:
    """Convert megabytes to bytes"""
    return int(mb_value * 1024 * 1024)

