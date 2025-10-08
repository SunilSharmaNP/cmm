# 23. start.sh - Enhanced startup script
# Enhanced VideoCompress Bot Startup Script v2.0

set -e

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}🎬 Enhanced VideoCompress Bot v2.0${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
}

print_header

# Check if Python is available
print_info "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python3 is not installed or not in PATH"
    print_info "Please install Python 3.8+ and try again"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
print_info "Python version: $PYTHON_VERSION"

# Check Python version (minimum 3.8)
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
    print_error "Python 3.8 or higher is required"
    print_info "Current version: $PYTHON_VERSION"
    exit 1
fi

# Check if FFmpeg is available
print_info "Checking FFmpeg installation..."
if ! command -v ffmpeg &> /dev/null; then
    print_warning "FFmpeg is not installed or not in PATH"
    print_info "The bot will not work without FFmpeg. Please install it:"
    echo "  Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  CentOS/RHEL: sudo yum install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    echo "  Windows: Download from https://ffmpeg.org/"
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    FFMPEG_VERSION=$(ffmpeg -version | head -n 1 | cut -d " " -f 3)
    print_info "FFmpeg version: $FFMPEG_VERSION"
fi

# Create necessary directories
print_info "Creating necessary directories..."
mkdir -p downloads logs temp

# Check for configuration
print_info "Checking configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        print_warning "No .env file found. Creating from .env.example"
        cp .env.example .env
        print_warning "Please edit .env file with your configuration before running the bot"
    else
        print_error "No configuration found. Please create .env file"
        exit 1
    fi
fi

# Load environment variables
if [ -f ".env" ]; then
    print_info "Loading environment variables..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Validate required environment variables
print_info "Validating configuration..."
required_vars=("TG_BOT_TOKEN" "APP_ID" "API_HASH" "AUTH_USERS")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    print_error "Missing required environment variables:"
    printf '  %s\\n' "${missing_vars[@]}"
    print_info "Please set these variables in your .env file"
    exit 1
fi

# Install/upgrade dependencies
print_info "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    if command -v pip3 &> /dev/null; then
        pip3 install --user --upgrade pip
        pip3 install --user -r requirements.txt
    else
        python3 -m pip install --user --upgrade pip
        python3 -m pip install --user -r requirements.txt
    fi
else
    print_warning "requirements.txt not found, skipping dependency installation"
fi

# Test database connection if configured
if [ -n "$DATABASE_URL" ]; then
    print_info "Testing database connection..."
    python3 -c "
import asyncio
import motor.motor_asyncio
import os
import sys

async def test_db():
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient('$DATABASE_URL', serverSelectionTimeoutMS=5000)
        await client.admin.command('ping')
        print('✅ Database connection successful')
        client.close()
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        sys.exit(1)

asyncio.run(test_db())
" || print_warning "Database connection test failed, but continuing anyway"
fi

# Show configuration summary
print_info "Configuration Summary:"
echo "  Bot Token: ${TG_BOT_TOKEN:0:10}..."
echo "  App ID: $APP_ID"
echo "  Auth Users: $AUTH_USERS"
echo "  Database: ${DATABASE_URL:0:20}..."
echo "  Log Channel: $LOG_CHANNEL"
echo ""

# Final check
print_info "Pre-flight checks completed successfully!"
print_info "Starting Enhanced VideoCompress Bot v2.0..."
echo "Sunil Sharma 2.O"

# Start the bot
exec python3 -m bot

