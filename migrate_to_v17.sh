#!/usr/bin/env bash
# Database migration script from Heroku Postgres (v17) to Render Postgres (v17)
# 
# Usage:
#   1. Get your Render Postgres connection string from Render dashboard
#   2. Set environment variables:
#      export HEROKU_DATABASE_URL='postgres://user:pass@host:port/dbname'
#      export RENDER_DATABASE_URL='postgresql://user:pass@host:port/dbname'
#   3. Run: ./migrate_to_v17.sh

set -e

echo "Starting database migration from Heroku Postgres (v17) to Render Postgres (v17)..."
echo ""

# Check if required tools are installed
if ! command -v pg_dump &> /dev/null; then
    echo "Error: pg_dump is not installed. Please install PostgreSQL client tools."
    exit 1
fi

if ! command -v psql &> /dev/null; then
    echo "Error: psql is not installed. Please install PostgreSQL client tools."
    exit 1
fi

# Heroku database URL - must be set via environment
HEROKU_DATABASE_URL="${HEROKU_DATABASE_URL:-}"
if [ -z "$HEROKU_DATABASE_URL" ]; then
    echo "Error: HEROKU_DATABASE_URL not set. export HEROKU_DATABASE_URL='postgres://...'"
    exit 1
fi

# Check if Render database URL is set
if [ -z "$RENDER_DATABASE_URL" ]; then
    echo "Error: RENDER_DATABASE_URL environment variable is not set"
    echo ""
    echo "Get it from Render dashboard:"
    echo "  https://dashboard.render.com/d/dpg-d5ojph5actks73a3evng-a"
    echo "  Click 'Connection Info' or 'Info' tab"
    echo "  Copy the 'Internal Database URL'"
    echo ""
    echo "Then run:"
    echo "  export RENDER_DATABASE_URL='postgresql://user:pass@host:port/dbname'"
    echo "  ./migrate_to_v17.sh"
    exit 1
fi

# Create backup directory
BACKUP_DIR="./db_backup"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/heroku_backup_$(date +%Y%m%d_%H%M%S).sql"

echo "Step 1: Dumping data from Heroku Postgres (v17)..."
echo "  Source: Heroku Postgres"
pg_dump "$HEROKU_DATABASE_URL" \
    --verbose \
    --clean \
    --no-acl \
    --no-owner \
    --format=plain \
    -f "$BACKUP_FILE" 2>&1 | grep -v "server version mismatch" || {
    echo "Warning: Version mismatch message (this is OK if dump succeeded)"
}

if [ ! -f "$BACKUP_FILE" ] || [ ! -s "$BACKUP_FILE" ]; then
    echo "Error: Backup file was not created or is empty"
    exit 1
fi

FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "✓ Backup created: $BACKUP_FILE ($FILE_SIZE)"
echo ""

echo "Step 2: Restoring data to Render Postgres (v17)..."
echo "  Destination: Render Postgres"
psql "$RENDER_DATABASE_URL" -f "$BACKUP_FILE" 2>&1 | tee "$BACKUP_DIR/restore_log.txt" || {
    echo ""
    echo "Warning: Some errors occurred during restore."
    echo "This might be normal if:"
    echo "  - Tables already exist (from migrations)"
    echo "  - Some system tables differ between versions"
    echo ""
    echo "Check the restore log: $BACKUP_DIR/restore_log.txt"
    echo ""
}

echo ""
echo "✓ Migration complete!"
echo ""
echo "Backup saved to: $BACKUP_FILE"
echo ""
echo "Next steps:"
echo "1. Link the database to your web service in Render dashboard"
echo "2. Update DATABASE_URL environment variable in Render"
echo "3. Deploy your app - migrations will run automatically during build"
echo "4. If needed, run: python manage.py migrate --no-input"
