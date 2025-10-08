# 2. bot/config.py - Enhanced configuration

from bot.get_cfg import get_config
import os

class Config(object):
    # Basic Configuration
    SESSION_NAME = get_config("SESSION_NAME", "EnhancedCompressorBot")
    DATABASE_URL = get_config("DATABASE_URL", "")
    TG_BOT_TOKEN = get_config("TG_BOT_TOKEN", "")
    
    # Telegram API Configuration
    APP_ID = int(get_config("APP_ID", "12345"))
    API_HASH = get_config("API_HASH", "")
    BOT_USERNAME = get_config("BOT_USERNAME", "")
    
    # Channel Configuration  
    LOG_CHANNEL = get_config("LOG_CHANNEL", "")
    UPDATES_CHANNEL = get_config("UPDATES_CHANNEL", None)
    
    # User Configuration
    AUTH_USERS = set(
        int(x) for x in get_config(
            "AUTH_USERS",
            "123456789"
        ).split()
    )
    
    # File Configuration
    DOWNLOAD_LOCATION = get_config("DOWNLOAD_LOCATION", "./downloads")
    MAX_FILE_SIZE = int(get_config("MAX_FILE_SIZE", "4294967296"))  # 4GB
    TG_MAX_FILE_SIZE = int(get_config("TG_MAX_FILE_SIZE", "2097152000"))  # 2GB
    FREE_USER_MAX_FILE_SIZE = int(get_config("FREE_USER_MAX_FILE_SIZE", "1073741824"))  # 1GB
    
    # Enhanced File Type Restrictions
    ALLOWED_FILE_TYPES = get_config(
        "ALLOWED_FILE_TYPES", 
        "mp4,mkv,avi,mov,wmv,flv,webm,m4v,3gp,ts,mts,m2ts"
    ).lower().split(',')
    
    # Progress Configuration
    MAX_MESSAGE_LENGTH = int(get_config("MAX_MESSAGE_LENGTH", "4096"))
    FINISHED_PROGRESS_STR = get_config("FINISHED_PROGRESS_STR", "▓")
    UN_FINISHED_PROGRESS_STR = get_config("UN_FINISHED_PROGRESS_STR", "░")
    
    # UI Configuration
    SHOULD_USE_BUTTONS = get_config("SHOULD_USE_BUTTONS", "True").lower() == "true"
    
    # Logging Configuration
    LOG_FILE_ZZGEVC = get_config("LOG_FILE_ZZGEVC", "logs/bot.log")
    
    # Enhanced Features Configuration
    MAX_CONCURRENT_PROCESSES = int(get_config("MAX_CONCURRENT_PROCESSES", "3"))
    ENABLE_QUEUE = str(get_config("ENABLE_QUEUE", "True")).lower() == "true"
    QUEUE_SIZE = int(get_config("QUEUE_SIZE", "10"))
    
    # Compression Configuration
    DEFAULT_COMPRESSION = int(get_config("DEFAULT_COMPRESSION", "50"))
    MIN_COMPRESSION = int(get_config("MIN_COMPRESSION", "10"))
    MAX_COMPRESSION = int(get_config("MAX_COMPRESSION", "90"))
    
    # Quality Presets
    COMPRESSION_PRESETS = {
        'high': {
            'video_codec': 'libx264',
            'preset': 'slow', 
            'crf': 18,
            'audio_codec': 'aac',
            'audio_bitrate': '128k'
        },
        'medium': {
            'video_codec': 'libx264', 
            'preset': 'medium',
            'crf': 23,
            'audio_codec': 'aac',
            'audio_bitrate': '96k'
        },
        'low': {
            'video_codec': 'libx264',
            'preset': 'ultrafast', 
            'crf': 28,
            'audio_codec': 'aac',
            'audio_bitrate': '64k'
        }
    }
    
    # Security Configuration
    RATE_LIMIT_MESSAGES = int(get_config("RATE_LIMIT_MESSAGES", "10"))
    RATE_LIMIT_WINDOW = int(get_config("RATE_LIMIT_WINDOW", "60"))  # seconds
    BAN_DURATION_FLOOD = int(get_config("BAN_DURATION_FLOOD", "3600"))  # 1 hour
    
    # Output Formats
    SUPPORTED_OUTPUT_FORMATS = ['mp4', 'mkv', 'webm', 'avi']
    DEFAULT_OUTPUT_FORMAT = get_config("DEFAULT_OUTPUT_FORMAT", "mp4")
    
    # Thumbnail Configuration
    DEF_THUMB_NAIL_VID_S = get_config(
        "DEF_THUMB_NAIL_VID_S", 
        "https://telegra.ph/file/4a48f5c40c68ac14be2f5.jpg"
    )
    CUSTOM_THUMBNAIL_ENABLED = get_config("CUSTOM_THUMBNAIL_ENABLED", "True").lower() == "true"
    
    # Network Configuration
    HTTP_PROXY = get_config("HTTP_PROXY", None)
    TIMEOUT_DOWNLOAD = int(get_config("TIMEOUT_DOWNLOAD", "3600"))  # 1 hour
    TIMEOUT_UPLOAD = int(get_config("TIMEOUT_UPLOAD", "3600"))  # 1 hour
    
    # Performance Configuration
    CHUNK_SIZE = int(get_config("CHUNK_SIZE", str(1024 * 1024)))  # 1MB chunks
    MAX_WORKERS = int(get_config("MAX_WORKERS", "4"))
    
    # Database Configuration
    DB_POOL_SIZE = int(get_config("DB_POOL_SIZE", "10"))
    DB_MAX_IDLE_TIME = int(get_config("DB_MAX_IDLE_TIME", "300"))  # 5 minutes
    
    # Backup Configuration
    ENABLE_BACKUP = get_config("ENABLE_BACKUP", "False").lower() == "true"
    BACKUP_CHANNEL = get_config("BACKUP_CHANNEL", None)
