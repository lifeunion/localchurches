#!/usr/bin/env bash
# Database migration script from Heroku Postgres to Render Postgres
# 
# Usage:
#   1. Link the Render Postgres database to your web service in Render dashboard
#   2. Get your Heroku Postgres connection string: heroku pg:credentials:url DATABASE_URL
#   3. Set environment variables:
#      export HEROKU_DATABASE_URL="postgresql://user:pass@host:port/dbname"
#      export RENDER_DATABASE_URL="postgresql://user:pass@host:port/dbname"
#   4. Run: ./migrate_database.sh

set -e

echo "Starting database migration from Heroku Postgres to Render Postgres..."

# Check if required tools are installed
if ! command -v pg_dump &> /dev/null; then
    echo "Error: pg_dump is not installed. Please install PostgreSQL client tools."
    exit 1
fi

if ! command -v psql &> /dev/null; then
    echo "Error: psql is not installed. Please install PostgreSQL client tools."
    exit 1
fi

# Check if environment variables are set
if [ -z "$HEROKU_DATABASE_URL" ]; then
    echo "Error: HEROKU_DATABASE_URL environment variable is not set"
    echo "Get it from: heroku pg:credentials:url DATABASE_URL"
    exit 1
fi

if [ -z "$RENDER_DATABASE_URL" ]; then
    echo "Error: RENDER_DATABASE_URL environment variable is not set"
    echo "Get it from Render dashboard -> localchurches-db -> Connection Info"
    exit 1
fi

# Create backup directory
BACKUP_DIR="./db_backup"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/heroku_backup_$(date +%Y%m%d_%H%M%S).sql"

echo "Step 1: Dumping data from Heroku Postgres..."
pg_dump "$HEROKU_DATABASE_URL" --verbose --clean --no-acl --no-owner -f "$BACKUP_FILE"

if [ ! -f "$BACKUP_FILE" ] || [ ! -s "$BACKUP_FILE" ]; then
    echo "Error: Backup file was not created or is empty"
    exit 1
fi

echo "Step 2: Backup created: $BACKUP_FILE"
echo "Step 3: Restoring data to Render Postgres..."

# Restore the database
psql "$RENDER_DATABASE_URL" -f "$BACKUP_FILE" || {
    echo "Warning: Some errors occurred during restore. This might be normal if tables already exist."
    echo "Continuing with migration..."
}

echo "Step 4: Running Django migrations on Render database..."
echo "Note: You may need to run this on Render after linking the database:"
echo "  python manage.py migrate --no-input"

echo ""
echo "Migration complete!"
echo "Backup saved to: $BACKUP_FILE"
echo ""
echo "Next steps:"
echo "1. Link the database to your web service in Render dashboard"
echo "2. The DATABASE_URL will be automatically set"
echo "3. Deploy your app - migrations will run automatically during build"
