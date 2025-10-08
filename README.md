# 25. README.md - Comprehensive documentation
repository_files['README.md'] = '''# 🎬 Enhanced VideoCompress Bot v2.0

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Pyrogram](https://img.shields.io/badge/Pyrogram-2.0+-green.svg)](https://pyrogram.org/)
[![License](https://img.shields.io/badge/license-GPL--3.0-red.svg)](COPYING)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](Dockerfile)
[![Maintenance](https://img.shields.io/badge/maintained-yes-green.svg)](https://github.com/enhanced/videocompress-bot/graphs/commit-activity)

> **An advanced Telegram video compression bot with cutting-edge features, built with modern Python and Pyrogram.**

Transform your video files with professional-grade compression while maintaining excellent quality. Perfect for content creators, developers, and anyone who needs efficient video processing through Telegram.

## ✨ Features Overview

### 🚀 Core Compression Features
- **🎯 Smart Quality Control** - Multiple compression presets (high, medium, low) + custom percentage
- **📱 Multi-Format Support** - Input: MP4, MKV, AVI, MOV, WEBM, FLV, WMV | Output: MP4, MKV, WEBM, AVI
- **⚡ Advanced FFmpeg Integration** - Professional video encoding with optimized settings
- **📊 Real-Time Progress** - Live progress tracking with ETA calculation and speed monitoring
- **🖼️ Custom Thumbnails** - Support for custom video thumbnails and auto-generation

### 🛡️ Advanced Management
- **📋 Queue System** - Handle multiple compression requests efficiently with priority management
- **👥 User Management** - Advanced ban/unban system with reasons and duration tracking
- **💾 Database Integration** - MongoDB for persistent data storage and user statistics
- **📈 Analytics Dashboard** - Detailed user and system statistics with performance monitoring

### 🔒 Security & Performance
- **🚫 Rate Limiting** - Intelligent spam prevention and abuse protection
- **🔐 Admin Controls** - Comprehensive administrative commands and system monitoring
- **⚙️ System Optimization** - CPU, memory, and disk usage tracking with auto-cleanup
- **🔄 Error Recovery** - Comprehensive error handling and automatic recovery

### 📡 Integration & Deployment
- **🐳 Docker Ready** - Complete containerization with Docker Compose support
- **☁️ Cloud Deploy** - One-click deployment to Heroku, Railway, and other platforms
- **🔧 Easy Setup** - Automated deployment scripts and configuration wizards
- **📊 Monitoring** - Health checks, logging, and performance metrics

## 📋 System Requirements

### Minimum Requirements
- **OS**: Linux (Ubuntu 18.04+), macOS (10.14+), Windows 10
- **Python**: 3.8 or higher
- **RAM**: 512MB (1GB+ recommended)
- **Storage**: 1GB free space
- **Network**: Stable internet connection

### Recommended Setup
- **CPU**: 2+ cores
- **RAM**: 2GB+ 
- **Storage**: 5GB+ free space
- **Database**: MongoDB 4.4+
- **FFmpeg**: Latest version

### Dependencies
```bash
# Core Python packages
pyrogram==2.0.106
motor>=3.0.0        # MongoDB driver
aiofiles>=22.1.0    # Async file operations
psutil>=5.9.0       # System monitoring
Pillow>=9.0.0       # Image processing
```

## 🚀 Quick Start Guide

### Method 1: Automated Deployment (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/enhanced/videocompress-bot.git
cd videocompress-bot

# 2. Run the deployment script
chmod +x deploy.sh
./deploy.sh

# 3. Configure your bot (the script will guide you)
# 4. Start the bot
./start_bot.sh
```

### Method 2: Manual Installation

```bash
# 1. Clone and enter directory
git clone https://github.com/enhanced/videocompress-bot.git
cd videocompress-bot

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\\Scripts\\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup configuration
cp .env.example .env
nano .env  # Edit with your values

# 5. Start the bot
python -m bot
```

### Method 3: Docker Deployment

```bash
# 1. Clone repository
git clone https://github.com/enhanced/videocompress-bot.git
cd videocompress-bot

# 2. Configure environment
cp .env.example .env
nano .env  # Add your configuration

# 3. Start with Docker Compose
docker-compose up -d

# 4. Check logs
docker-compose logs -f
```

## ⚙️ Configuration Guide

### Required Environment Variables

Create a `.env` file with these essential settings:

```env
# 🤖 Bot Configuration
TG_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxyz  # From @BotFather
APP_ID=12345678                                      # From my.telegram.org
API_HASH=abcdef1234567890abcdef1234567890            # From my.telegram.org
BOT_USERNAME=your_bot_username                       # Without @ symbol

# 👨‍💼 Admin Configuration  
AUTH_USERS=123456789 987654321                      # Space-separated admin user IDs
LOG_CHANNEL=@your_log_channel                       # Channel for bot logs

# 💾 Database Configuration
DATABASE_URL=mongodb://localhost:27017/videocompressbot  # MongoDB connection string
```

### Optional Advanced Settings

```env
# 📺 Force Subscription (Optional)
UPDATES_CHANNEL=your_updates_channel    # Force users to join this channel

# 🎛️ Compression Settings
DEFAULT_COMPRESSION=50                  # Default compression percentage (10-90)
MAX_CONCURRENT_PROCESSES=3             # Max simultaneous compressions
QUEUE_SIZE=10                          # Maximum queue length

# 📁 File Configuration
MAX_FILE_SIZE=4294967296               # 4GB max file size
ALLOWED_FILE_TYPES=mp4,mkv,avi,mov,wmv,flv,webm

# 🚦 Rate Limiting
RATE_LIMIT_MESSAGES=10                 # Messages per time window
RATE_LIMIT_WINDOW=60                   # Time window in seconds
BAN_DURATION_FLOOD=3600                # Auto-ban duration for flooding
```

### Getting Required Values

1. **Bot Token**: Message [@BotFather](https://t.me/BotFather) on Telegram
2. **API Credentials**: Visit [my.telegram.org](https://my.telegram.org)
3. **User IDs**: Message [@userinfobot](https://t.me/userinfobot)
4. **MongoDB**: Use [MongoDB Atlas](https://cloud.mongodb.com/) for free cloud database

## 🎮 Usage Guide

### For Users

#### Basic Commands
```
/start          - Initialize the bot and see welcome message
/help           - Display detailed help and usage instructions
/compress       - Compress video with automatic quality detection
/compress 50    - Compress video to 50% of original size
/compress high  - Use high quality preset (25% compression)
/compress medium- Use medium quality preset (50% compression)  
/compress low   - Use low quality preset (75% compression)
```

#### How to Compress Videos
1. **Send your video** to the bot (up to 2GB)
2. **Reply to the video** with `/compress` command
3. **Choose quality** (optional): add quality after command
4. **Wait for processing** - you'll see real-time progress
5. **Download result** - compressed video with preserved quality

#### Supported Formats
- **Input**: MP4, MKV, AVI, MOV, WEBM, FLV, WMV, M4V, 3GP, TS, MTS, M2TS
- **Output**: MP4, MKV, WEBM, AVI
- **Quality**: Lossless to highly compressed with smart encoding

### For Administrators

#### Admin Commands
```
/status         - View detailed bot and system statistics
/ban <user_id>  - Ban user with optional duration and reason
/unban <user_id>- Remove ban from user
/banned_users   - List all banned users with details
/broadcast      - Send message to all users (reply to message)
/logs           - Download bot log files
/exec <command> - Execute system commands (use carefully)
/cancel         - Cancel current compression process
```

#### Advanced Management
```bash
# System monitoring
/stats          # Detailed system resource usage
/clean          # Clean temporary files and optimize storage
/backup         # Create database backup
/restart        # Safely restart the bot

# User analytics
/users active   # Show active user statistics
/users growth   # User growth analytics
/compress stats # Compression usage statistics
```

## 🐳 Docker Deployment

### Simple Docker Setup

```yaml
# docker-compose.yml
version: '3.8'
services:
  bot:
    build: .
    environment:
      - TG_BOT_TOKEN=your_token_here
      - APP_ID=your_app_id
      - API_HASH=your_api_hash  
      - DATABASE_URL=mongodb://mongo:27017/videobot
      - AUTH_USERS=your_user_id
    volumes:
      - ./downloads:/app/downloads
      - ./logs:/app/logs
    depends_on:
      - mongo

  mongo:
    image: mongo:5
    volumes:
      - mongo_data:/data/db

volumes:
  mongo_data:
```

### Production Docker Setup

```bash
# Advanced production deployment
docker-compose -f docker-compose.prod.yml up -d

# With monitoring and reverse proxy
docker-compose -f docker-compose.prod.yml -f docker-compose.monitoring.yml up -d

# Scale horizontally  
docker-compose up --scale bot=3 -d
```

## ☁️ Cloud Deployment

### Heroku Deployment

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/enhanced/videocompress-bot)

```bash
# Manual Heroku deployment
git clone https://github.com/enhanced/videocompress-bot.git
cd videocompress-bot
heroku create your-bot-name
heroku config:set TG_BOT_TOKEN=your_token
heroku config:set APP_ID=your_app_id
# ... set other variables
git push heroku main
```

### Railway Deployment

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template/your-template)

### VPS Deployment

```bash
# Ubuntu/Debian VPS
curl -sSL https://raw.githubusercontent.com/enhanced/videocompress-bot/main/scripts/vps-install.sh | bash

# CentOS/RHEL VPS  
curl -sSL https://raw.githubusercontent.com/enhanced/videocompress-bot/main/scripts/centos-install.sh | bash
```

## 🔧 Advanced Configuration

### Custom Compression Presets

```python
# In bot/config.py
COMPRESSION_PRESETS = {
    'ultra_high': {
        'video_codec': 'libx264',
        'preset': 'veryslow',
        'crf': 15,
        'audio_codec': 'flac'
    },
    'streaming': {
        'video_codec': 'libx264', 
        'preset': 'fast',
        'crf': 23,
        'audio_codec': 'aac',
        'optimize_streaming': True
    },
    'mobile': {
        'video_codec': 'libx264',
        'preset': 'fast', 
        'crf': 28,
        'resolution': '720p',
        'audio_codec': 'aac'
    }
}
```

### Database Optimization

```python
# MongoDB optimization settings
DB_CONFIG = {
    'maxPoolSize': 50,
    'minPoolSize': 5,
    'maxIdleTimeMS': 300000,
    'serverSelectionTimeoutMS': 5000,
    'connectTimeoutMS': 10000,
    'socketTimeoutMS': 10000
}
```

### Performance Tuning

```env
# Performance optimization
MAX_WORKERS=8                    # Increase for more powerful servers
CHUNK_SIZE=2097152              # 2MB chunks for faster processing
ENABLE_CACHING=True             # Enable result caching
CACHE_TTL=3600                  # Cache timeout in seconds
OPTIMIZE_THUMBNAILS=True        # Generate optimized thumbnails
```

## 📊 Monitoring & Analytics

### Built-in Metrics
- **User Statistics**: Total users, active users, growth trends
- **Compression Analytics**: Success rates, processing times, file sizes
- **System Metrics**: CPU, memory, disk usage, network I/O
- **Error Tracking**: Failed compressions, system errors, user issues

### External Monitoring Integration

```python
# Prometheus metrics (optional)
ENABLE_PROMETHEUS=True
PROMETHEUS_PORT=8080

# Grafana dashboard
GRAFANA_DASHBOARD_URL=your_grafana_url

# Health check endpoint
HEALTH_CHECK_PORT=8081
```

### Log Management

```bash
# View real-time logs
tail -f logs/bot.log

# Search for errors
grep -i error logs/bot.log

# Analyze performance
grep "compression completed" logs/bot.log | awk '{print $NF}'

# Log rotation (automatic)
# Logs are automatically rotated when they exceed 50MB
```

## 🛠️ Development Guide

### Setting Up Development Environment

```bash
# Clone with development dependencies
git clone https://github.com/enhanced/videocompress-bot.git
cd videocompress-bot

# Create development environment  
python -m venv dev-env
source dev-env/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Code formatting
black bot/
flake8 bot/

# Type checking
mypy bot/
```

### Project Structure

```
enhanced-videocompress-bot/
├── bot/                    # Main bot package
│   ├── __init__.py        # Bot initialization
│   ├── config.py          # Configuration management
│   ├── database/          # Database models and operations
│   ├── helper_funcs/      # Utility functions
│   ├── plugins/           # Command handlers
│   └── localization.py   # Multi-language support
├── docs/                  # Documentation
├── scripts/               # Deployment and utility scripts
├── tests/                 # Unit and integration tests
├── docker-compose.yml     # Docker configuration
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

### Contributing Guidelines

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes with proper tests
4. **Commit** with descriptive messages (`git commit -m 'Add amazing feature'`)
5. **Push** to your branch (`git push origin feature/amazing-feature`)
6. **Open** a Pull Request with detailed description

### Code Style

- **PEP 8** compliance for Python code
- **Type hints** for better code documentation
- **Docstrings** for all functions and classes
- **Async/await** for all I/O operations
- **Error handling** for all external operations

## 🚨 Troubleshooting

### Common Issues and Solutions

#### Bot Won't Start
```bash
# Check Python version
python3 --version  # Should be 3.8+

# Verify dependencies
pip check

# Check configuration
python -c "from bot.config import Config; print('Config OK')"

# View detailed logs
tail -f logs/bot.log
```

#### FFmpeg Issues
```bash
# Install FFmpeg (Ubuntu/Debian)
sudo apt update && sudo apt install ffmpeg

# Install FFmpeg (macOS)
brew install ffmpeg

# Verify installation
ffmpeg -version

# Test basic functionality
ffmpeg -f lavfi -i testsrc -t 1 -y test.mp4 && rm test.mp4
```

#### Database Connection Problems
```bash
# Test MongoDB connection
python -c "
import motor.motor_asyncio
import asyncio
async def test():
    client = motor.motor_asyncio.AsyncIOMotorClient('your_db_url')
    await client.admin.command('ping')
    print('Database OK')
asyncio.run(test())
"

# Check MongoDB Atlas IP whitelist
# Ensure 0.0.0.0/0 is added for cloud deployments
```

#### Memory/Performance Issues
```bash
# Check system resources
htop
df -h

# Monitor bot resource usage
ps aux | grep python

# Clear temporary files
./scripts/cleanup.sh

# Reduce concurrent processes in .env
MAX_CONCURRENT_PROCESSES=1
```

#### Compression Failures
```bash
# Check FFmpeg logs
tail -f logs/ffmpeg.log

# Test with smaller file
# Try different quality settings
# Verify input file integrity

# Common solutions:
# - Reduce compression quality
# - Update FFmpeg
# - Check available disk space
```

### Getting Help

- **📖 Documentation**: [GitHub Wiki](https://github.com/enhanced/videocompress-bot/wiki)
- **🐛 Bug Reports**: [GitHub Issues](https://github.com/enhanced/videocompress-bot/issues)
- **💬 Community Support**: [Telegram Group](https://t.me/linux_repo)
- **📢 Updates**: [Telegram Channel](https://t.me/Discovery_Updates)
- **💌 Direct Contact**: Create an issue with `question` label

## 📄 License & Legal

### License
This project is licensed under the **GNU General Public License v3.0**. See the [COPYING](COPYING) file for full details.

### Disclaimer
- This bot is for **educational and personal use** only
- Users are responsible for **complying with local laws** regarding video processing
- The developers are **not liable** for any misuse or legal issues
- **Respect copyright** and intellectual property rights

### Privacy Policy
- We **do not store** processed videos on our servers
- User data is **encrypted** and stored securely
- Analytics data is **anonymized** and used only for improvement
- Users can **request data deletion** at any time

## 🙏 Credits & Acknowledgments

### Original Authors
- **[@AbirHasan2005](https://github.com/AbirHasan2005)** - Original VideoCompress Bot creator
- **Enhanced Development Team** - Advanced features and improvements

### Dependencies & Libraries
- **[Pyrogram](https://pyrogram.org/)** - Modern Telegram Bot API framework
- **[FFmpeg](https://ffmpeg.org/)** - Multimedia processing powerhouse  
- **[MongoDB](https://www.mongodb.com/)** - NoSQL database for data persistence
- **[Docker](https://www.docker.com/)** - Containerization platform

### Community Contributors
- **Beta Testers** - Early adopters who helped identify issues
- **Translators** - Multi-language support contributors
- **Code Contributors** - Developers who submitted pull requests
- **Bug reporters** - Users who reported issues and suggested improvements

### Special Thanks
- **Telegram** - For providing excellent Bot API
- **Open Source Community** - For inspiration and code examples
- **Users** - For feedback, suggestions, and continuous support

---

<div align="center">

### 🎬 Enhanced VideoCompress Bot v2.0

**The Ultimate Telegram Video Compression Solution**

[⭐ Star this repo](https://github.com/enhanced/videocompress-bot) • [🐛 Report Bug](https://github.com/enhanced/videocompress-bot/issues) • [💡 Request Feature](https://github.com/enhanced/videocompress-bot/issues) • [💬 Join Community](https://t.me/linux_repo)

**Made with ❤️ by the Enhanced Development Team**

*Transforming videos, one compression at a time* ✨

</div>

---

### 📈 Project Statistics

![GitHub stars](https://img.shields.io/github/stars/enhanced/videocompress-bot?style=social)
![GitHub forks](https://img.shields.io/github/forks/enhanced/videocompress-bot?style=social)
![GitHub issues](https://img.shields.io/github/issues/enhanced/videocompress-bot)
![GitHub pull requests](https://img.shields.io/github/issues-pr/enhanced/videocompress-bot)
![GitHub contributors](https://img.shields.io/github/contributors/enhanced/videocompress-bot)
![GitHub last commit](https://img.shields.io/github/last-commit/enhanced/videocompress-bot)
'''

print("Created deployment script and README")
