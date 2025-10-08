# 31. scripts/install.sh - Quick install script

# Quick installation script for Enhanced VideoCompress Bot v2.0

set -e

echo "🚀 Installing Enhanced VideoCompress Bot v2.0..."

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Install system dependencies
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y ffmpeg python3-pip python3-venv
elif command -v brew &> /dev/null; then
    brew install ffmpeg
fi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Setup configuration
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️ Please edit .env file with your configuration"
fi

echo "✅ Installation completed!"
echo "📝 Edit .env file and run: ./start.sh"
