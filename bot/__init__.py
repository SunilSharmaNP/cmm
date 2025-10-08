#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 1. bot/__init__.py – Enhanced initialization FIXED
# Ensures DOWNLOAD_LOCATION is absolute and directories are created before handlers load

import logging
from logging.handlers import RotatingFileHandler
import os
import time
import sys

# Import Config early so we can override DOWNLOAD_LOCATION if needed
from bot.config import Config

# Override download location to absolute path inside container
DOWNLOAD_LOCATION = getattr(Config, "DOWNLOAD_LOCATION", "/app/downloads")
if not os.path.isabs(DOWNLOAD_LOCATION):
    DOWNLOAD_LOCATION = os.path.join("/app", DOWNLOAD_LOCATION.lstrip("./"))

# Log directory
LOG_FILE_ZZGEVC = getattr(Config, "LOG_FILE_ZZGEVC", "logs/bot.log")
LOG_DIR = os.path.dirname(LOG_FILE_ZZGEVC) or "logs"

# Create necessary directories immediately
os.makedirs(DOWNLOAD_LOCATION, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs("temp", exist_ok=True)

# Enhanced Configuration Loading
try:
    SESSION_NAME = Config.SESSION_NAME
    TG_BOT_TOKEN = Config.TG_BOT_TOKEN
    APP_ID = Config.APP_ID
    API_HASH = Config.API_HASH
    AUTH_USERS = list(set(Config.AUTH_USERS))
    DEFAULT_ADMINS = [715779594, 144528371]
    for admin in DEFAULT_ADMINS:
        if admin not in AUTH_USERS:
            AUTH_USERS.append(admin)
    LOG_CHANNEL = Config.LOG_CHANNEL
    DATABASE_URL = Config.DATABASE_URL
    MAX_FILE_SIZE = Config.MAX_FILE_SIZE
    TG_MAX_FILE_SIZE = Config.TG_MAX_FILE_SIZE
    FREE_USER_MAX_FILE_SIZE = Config.FREE_USER_MAX_FILE_SIZE
    MAX_MESSAGE_LENGTH = Config.MAX_MESSAGE_LENGTH
    FINISHED_PROGRESS_STR = Config.FINISHED_PROGRESS_STR
    UN_FINISHED_PROGRESS_STR = Config.UN_FINISHED_PROGRESS_STR
    SHOULD_USE_BUTTONS = Config.SHOULD_USE_BUTTONS
    BOT_START_TIME = time.time()
    BOT_USERNAME = Config.BOT_USERNAME
    UPDATES_CHANNEL = Config.UPDATES_CHANNEL
    MAX_CONCURRENT_PROCESSES = Config.MAX_CONCURRENT_PROCESSES
    ENABLE_QUEUE = Config.ENABLE_QUEUE
    ALLOWED_FILE_TYPES = Config.ALLOWED_FILE_TYPES
    COMPRESSION_PRESETS = Config.COMPRESSION_PRESETS
except Exception as e:
    print(f"Configuration Error: {e}")
    print("Please check your environment variables and config.py file")
    sys.exit(1)

# Initialize log file (truncate if exists)
if os.path.exists(LOG_FILE_ZZGEVC):
    with open(LOG_FILE_ZZGEVC, "r+"):
        open(LOG_FILE_ZZGEVC, "w").close()

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

# Suppress noisy loggers
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

LOGGER = logging.getLogger(__name__)
LOGGER.info("Enhanced VideoCompress Bot v2.0 initialized successfully!")
LOGGER.info(f"Download directory: {DOWNLOAD_LOCATION}")
LOGGER.info(f"Log directory: {LOG_DIR}")
