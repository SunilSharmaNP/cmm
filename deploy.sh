# 24. deploy.sh - Enhanced deployment script
# Enhanced VideoCompress Bot Deployment Script v2.0

set -e

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
PURPLE='\\033[0;35m'
NC='\\033[0m'

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}🚀 Enhanced VideoCompress Bot v2.0${NC}"
    echo -e "${BLUE}🛠️  Advanced Deployment Script${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
}

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

print_header

# Check if script is run as root (not recommended)
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root is not recommended for security reasons"
    print_info "Consider creating a dedicated user for the bot"
fi

# System requirements check
print_step "Checking system requirements..."

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    print_info "Install Python 3.8+ and try again"
    exit 1
fi

python_version=$(python3 --version | cut -d " " -f 2 | cut -d "." -f 1,2)
if [ "$(printf '%s\\n' "3.8" "$python_version" | sort -V | head -n1)" != "3.8" ]; then
    print_error "Python 3.8 or higher is required. Current: $python_version"
    exit 1
fi

print_success "Python $python_version ✓"

# Check for required tools
tools=("git" "curl" "wget")
for tool in "${tools[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        print_error "$tool is required but not installed"
        exit 1
    fi
done

# Install system dependencies
print_step "Installing system dependencies..."

if command -v apt-get &> /dev/null; then
    print_info "Detected Debian/Ubuntu system"
    sudo apt-get update
    sudo apt-get install -y ffmpeg python3-pip python3-venv
elif command -v yum &> /dev/null; then
    print_info "Detected RHEL/CentOS system"
    sudo yum install -y epel-release
    sudo yum install -y ffmpeg python3-pip
elif command -v dnf &> /dev/null; then
    print_info "Detected Fedora system"
    sudo dnf install -y ffmpeg python3-pip
elif command -v pacman &> /dev/null; then
    print_info "Detected Arch Linux system"
    sudo pacman -S --noconfirm ffmpeg python-pip
elif command -v brew &> /dev/null; then
    print_info "Detected macOS with Homebrew"
    brew install ffmpeg
else
    print_warning "Could not detect package manager"
    print_info "Please install FFmpeg manually"
fi

# Verify FFmpeg installation
if command -v ffmpeg &> /dev/null; then
    ffmpeg_version=$(ffmpeg -version | head -n 1 | cut -d " " -f 3)
    print_success "FFmpeg $ffmpeg_version ✓"
else
    print_error "FFmpeg installation failed"
    exit 1
fi

# Create project directory structure
print_step "Setting up project structure..."

mkdir -p downloads logs temp backups
chmod 755 downloads logs temp backups

print_success "Directory structure created ✓"

# Python virtual environment setup
print_step "Setting up Python virtual environment..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_info "Virtual environment created"
else
    print_info "Virtual environment already exists"
fi

source venv/bin/activate
pip install --upgrade pip setuptools wheel

print_success "Virtual environment ready ✓"

# Install Python dependencies
print_step "Installing Python dependencies..."

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_success "Dependencies installed ✓"
else
    print_error "requirements.txt not found"
    exit 1
fi

# Configuration setup
print_step "Setting up configuration..."

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_info "Created .env from .env.example"
        print_warning "Please edit .env file with your actual values"
    else
        print_error ".env.example not found"
        exit 1
    fi
else
    print_info ".env file already exists"
fi

# Interactive configuration (optional)
read -p "Do you want to configure the bot interactively? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_step "Interactive configuration..."
    
    read -p "Enter your Bot Token: " bot_token
    read -p "Enter your App ID: " app_id
    read -p "Enter your API Hash: " api_hash
    read -p "Enter your User ID (admin): " user_id
    read -p "Enter your Bot Username (without @): " bot_username
    read -p "Enter your Log Channel (with @): " log_channel
    
    # Update .env file
    sed -i "s/TG_BOT_TOKEN=.*/TG_BOT_TOKEN=$bot_token/" .env
    sed -i "s/APP_ID=.*/APP_ID=$app_id/" .env
    sed -i "s/API_HASH=.*/API_HASH=$api_hash/" .env
    sed -i "s/AUTH_USERS=.*/AUTH_USERS=$user_id/" .env
    sed -i "s/BOT_USERNAME=.*/BOT_USERNAME=$bot_username/" .env
    sed -i "s/LOG_CHANNEL=.*/LOG_CHANNEL=$log_channel/" .env
    
    print_success "Configuration updated ✓"
fi

# Database setup (MongoDB)
print_step "Setting up database..."

if command -v docker &> /dev/null; then
    read -p "Do you want to set up MongoDB using Docker? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Starting MongoDB container..."
        docker run -d \\
            --name videocompress-mongodb \\
            -p 27017:27017 \\
            -v mongodb_data:/data/db \\
            --restart unless-stopped \\
            mongo:5-focal
        
        # Update database URL in .env
        sed -i "s|DATABASE_URL=.*|DATABASE_URL=mongodb://localhost:27017/videocompressbot|" .env
        print_success "MongoDB container started ✓"
    fi
fi

# Systemd service setup (Linux only)
if command -v systemctl &> /dev/null && [ "$EUID" -ne 0 ]; then
    read -p "Do you want to create a systemd service? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_step "Creating systemd service..."
        
        service_content="[Unit]
Description=Enhanced VideoCompress Bot v2.0
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$PWD
Environment=PATH=$PWD/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$PWD/venv/bin/python -m bot
ExecReload=/bin/kill -HUP \\$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target"

        echo "$service_content" | sudo tee /etc/systemd/system/enhanced-videocompress-bot.service > /dev/null
        sudo systemctl daemon-reload
        
        print_success "Systemd service created ✓"
        print_info "Service management commands:"
        print_info "  Start: sudo systemctl start enhanced-videocompress-bot"
        print_info "  Stop: sudo systemctl stop enhanced-videocompress-bot"
        print_info "  Enable auto-start: sudo systemctl enable enhanced-videocompress-bot"
        print_info "  View logs: sudo journalctl -u enhanced-videocompress-bot -f"
    fi
fi

# Create convenience scripts
print_step "Creating convenience scripts..."

# Start script
cat > start_bot.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python -m bot
EOF

# Stop script
cat > stop_bot.sh << 'EOF'
#!/bin/bash
pkill -f "python -m bot"
echo "Bot stopped"
EOF

# Update script
cat > update_bot.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
git pull origin main
source venv/bin/activate
pip install --upgrade -r requirements.txt
echo "Bot updated. Restart to apply changes."
EOF

# Status script
cat > status_bot.sh << 'EOF'
#!/bin/bash
if pgrep -f "python -m bot" > /dev/null; then
    echo "✅ Bot is running"
    echo "PID: $(pgrep -f "python -m bot")"
else
    echo "❌ Bot is not running"
fi
EOF

chmod +x start_bot.sh stop_bot.sh update_bot.sh status_bot.sh

print_success "Convenience scripts created ✓"

# Final configuration validation
print_step "Validating configuration..."

source .env

required_vars=("TG_BOT_TOKEN" "APP_ID" "API_HASH" "AUTH_USERS")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ] || [[ "${!var}" == *"your_"* ]] || [[ "${!var}" == *"123456"* ]]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    print_warning "The following variables need to be configured:"
    printf '  %s\\n' "${missing_vars[@]}"
    print_info "Please edit .env file with your actual values"
fi

# Test bot configuration
print_step "Testing bot configuration..."

python3 << 'EOF'
import os
import sys
from pyrogram import Client

try:
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    app_id = os.getenv('APP_ID')
    api_hash = os.getenv('API_HASH')
    bot_token = os.getenv('TG_BOT_TOKEN')
    
    if not all([app_id, api_hash, bot_token]):
        print("❌ Missing required configuration")
        sys.exit(1)
    
    # Test client creation
    client = Client(
        "test_session",
        api_id=int(app_id),
        api_hash=api_hash,
        bot_token=bot_token
    )
    
    print("✅ Bot configuration is valid")
    
    # Clean up test session
    import glob
    for file in glob.glob("test_session.*"):
        os.remove(file)
        
except ImportError:
    print("⚠️ python-dotenv not installed, skipping configuration test")
except Exception as e:
    print(f"❌ Configuration test failed: {e}")
    sys.exit(1)
EOF

print_success "Configuration test passed ✓"

# Deployment summary
print_step "Deployment Summary"
echo ""
echo "🎉 Enhanced VideoCompress Bot v2.0 deployment completed!"
echo ""
echo "📁 Project Structure:"
echo "  ├── bot/                 # Bot source code"
echo "  ├── downloads/           # Download directory"
echo "  ├── logs/                # Log files"
echo "  ├── temp/                # Temporary files"
echo "  ├── venv/                # Python virtual environment"
echo "  ├── .env                 # Configuration file"
echo "  └── *.sh                 # Management scripts"
echo ""
echo "🚀 To start the bot:"
echo "  ./start_bot.sh"
echo ""
echo "🛠️  Management commands:"
echo "  ./start_bot.sh           # Start the bot"
echo "  ./stop_bot.sh            # Stop the bot"
echo "  ./status_bot.sh          # Check bot status"
echo "  ./update_bot.sh          # Update the bot"
echo ""
echo "📖 Documentation:"
echo "  Check README.md for detailed usage instructions"
echo "  Visit: https://github.com/enhanced/videocompress-bot/wiki"
echo ""
echo "💬 Support:"
echo "  Updates: https://t.me/Discovery_Updates"
echo "  Support: https://t.me/linux_repo"
echo ""

if [ ${#missing_vars[@]} -ne 0 ]; then
    print_warning "⚠️  Don't forget to configure the missing variables in .env file!"
else
    print_success "✅ All configuration looks good! You can start the bot now."
fi

print_info "Happy video compressing! 🎬✨"

