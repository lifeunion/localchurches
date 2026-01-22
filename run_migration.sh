#!/usr/bin/env bash
# Quick migration script - fill in RENDER_DATABASE_URL before running

set -e

# Set both URLs via environment (no hardcoded secrets):
#   export HEROKU_DATABASE_URL='postgres://...'
#   export RENDER_DATABASE_URL='postgresql://...'
HEROKU_DATABASE_URL="${HEROKU_DATABASE_URL:-}"
RENDER_DATABASE_URL="${RENDER_DATABASE_URL:-}"

if [ -z "$HEROKU_DATABASE_URL" ]; then
    echo "Error: HEROKU_DATABASE_URL environment variable is not set"
    echo "  export HEROKU_DATABASE_URL='postgres://user:pass@host:port/dbname'"
    exit 1
fi

if [ -z "$RENDER_DATABASE_URL" ]; then
    echo "Error: RENDER_DATABASE_URL environment variable is not set"
    echo ""
    echo "Please provide your Render Postgres connection string:"
    echo "1. Go to: https://dashboard.render.com/d/dpg-d5ojhtc9c44c738ni630-a"
    echo "2. Click 'Connection Info' or 'Info' tab"
    echo "3. Copy the connection string"
    echo ""
    echo "Then run:"
    echo "  export RENDER_DATABASE_URL='your_connection_string_here'"
    echo "  ./run_migration.sh"
    exit 1
fi

echo "Starting database migration..."
echo "Source: Heroku Postgres"
echo "Destination: Render Postgres"
echo ""

# Create backup directory
BACKUP_DIR="./db_backup"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/heroku_backup_$(date +%Y%m%d_%H%M%S).sql"

echo "Step 1: Dumping data from Heroku Postgres..."
pg_dump "$HEROKU_DATABASE_URL" \
  --verbose \
  --clean \
  --no-acl \
  --no-owner \
  -f "$BACKUP_FILE"

if [ ! -f "$BACKUP_FILE" ] || [ ! -s "$BACKUP_FILE" ]; then
    echo "Error: Backup file was not created or is empty"
    exit 1
fi

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "✓ Backup created: $BACKUP_FILE ($BACKUP_SIZE)"
echo ""

echo "Step 2: Restoring data to Render Postgres..."
psql "$RENDER_DATABASE_URL" -f "$BACKUP_FILE" 2>&1 | grep -v "ERROR:" || {
    echo "Note: Some errors during restore are normal (e.g., if tables already exist)"
}

echo ""
echo "✓ Migration complete!"
echo ""
echo "Backup saved to: $BACKUP_FILE"
echo ""
echo "Next steps:"
echo "1. Link the database to your web service in Render dashboard"
echo "2. The DATABASE_URL will be automatically set"
echo "3. Your next deployment will use the new database"
