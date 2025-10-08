# 1. bot/__init__.py - Enhanced initialization

import logging
from logging.handlers import RotatingFileHandler
import os
import time
import sys
from bot.config import Config

# Enhanced Configuration Loading
try:
    SESSION_NAME = Config.SESSION_NAME
    TG_BOT_TOKEN = Config.TG_BOT_TOKEN
    APP_ID = Config.APP_ID
    API_HASH = Config.API_HASH
    AUTH_USERS = set(Config.AUTH_USERS)
    AUTH_USERS = list(AUTH_USERS)

    # Add default admin users (you can modify these)
    DEFAULT_ADMINS = [715779594, 144528371]
    for admin in DEFAULT_ADMINS:
        if admin not in AUTH_USERS:
            AUTH_USERS.append(admin)

    LOG_CHANNEL = Config.LOG_CHANNEL
    DATABASE_URL = Config.DATABASE_URL
    DOWNLOAD_LOCATION = Config.DOWNLOAD_LOCATION
    MAX_FILE_SIZE = Config.MAX_FILE_SIZE
    TG_MAX_FILE_SIZE = Config.TG_MAX_FILE_SIZE
    FREE_USER_MAX_FILE_SIZE = Config.FREE_USER_MAX_FILE_SIZE
    MAX_MESSAGE_LENGTH = Config.MAX_MESSAGE_LENGTH
    FINISHED_PROGRESS_STR = Config.FINISHED_PROGRESS_STR
    UN_FINISHED_PROGRESS_STR = Config.UN_FINISHED_PROGRESS_STR
    SHOULD_USE_BUTTONS = Config.SHOULD_USE_BUTTONS
    BOT_START_TIME = time.time()
    LOG_FILE_ZZGEVC = Config.LOG_FILE_ZZGEVC
    BOT_USERNAME = Config.BOT_USERNAME
    UPDATES_CHANNEL = Config.UPDATES_CHANNEL

    # Enhanced Features
    MAX_CONCURRENT_PROCESSES = Config.MAX_CONCURRENT_PROCESSES
    ENABLE_QUEUE = Config.ENABLE_QUEUE
    ALLOWED_FILE_TYPES = Config.ALLOWED_FILE_TYPES
    COMPRESSION_PRESETS = Config.COMPRESSION_PRESETS
    
except Exception as e:
    print(f"Configuration Error: {e}")
    print("Please check your environment variables and config.py file")
    sys.exit(1)

# Initialize log file
if os.path.exists(LOG_FILE_ZZGEVC):
    with open(LOG_FILE_ZZGEVC, "r+") as f_d:
        f_d.truncate(0)

# Create necessary directories
os.makedirs(os.path.dirname(LOG_FILE_ZZGEVC), exist_ok=True)
os.makedirs(DOWNLOAD_LOCATION, exist_ok=True)
os.makedirs("temp", exist_ok=True)

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(name)s:%(lineno)d] - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler(
            LOG_FILE_ZZGEVC,
            maxBytes=FREE_USER_MAX_FILE_SIZE,
            backupCount=10
        ),
        logging.StreamHandler(sys.stdout)
    ]
)

# Set appropriate log levels
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

LOGGER = logging.getLogger(__name__)
LOGGER.info("Enhanced VideoCompress Bot v2.0 initialized successfully!")
'''

print("Created bot/__init__.py")
