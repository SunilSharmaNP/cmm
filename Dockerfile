# 19. Dockerfile - Enhanced Docker configuration
FROM python:3.10-slim

# Set environment variables for better Python behavior
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    # FFmpeg for video processing
    ffmpeg \\
    # Basic utilities
    wget \\
    curl \\
    git \\
    # Build tools for Python packages
    build-essential \\
    pkg-config \\
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \\
    && apt-get clean

# Create non-root user for security
RUN groupadd -r botuser && useradd -r -g botuser -d /app -s /bin/bash botuser

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \\
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /app/downloads /app/logs /app/temp \\
    && chown -R botuser:botuser /app \\
    && chmod +x /app/start.sh /app/deploy.sh

# Switch to non-root user
USER botuser

# Expose port for health checks (optional)
EXPOSE 8080

# Health check to ensure bot is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import os; exit(0 if os.path.exists('/app/logs/bot.log') else 1)"

# Default command to run the bot
CMD ["python", "-m", "bot"]
