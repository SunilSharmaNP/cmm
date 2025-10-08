# 32. scripts/backup.sh - Database backup script
# Database backup script for Enhanced VideoCompress Bot v2.0

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/videocompress_backup_$DATE.json"

mkdir -p "$BACKUP_DIR"

echo "📦 Creating database backup..."

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not found in .env"
    exit 1
fi

# Create backup using mongodump
mongodump --uri="$DATABASE_URL" --out="$BACKUP_DIR/dump_$DATE"

echo "✅ Backup created: $BACKUP_DIR/dump_$DATE"
echo "📁 Backup size: $(du -sh "$BACKUP_DIR/dump_$DATE" | cut -f1)"
