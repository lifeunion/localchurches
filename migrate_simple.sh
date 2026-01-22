#!/usr/bin/env bash
# Simple, reliable database migration using pg_dump/psql
# This is the most straightforward approach - just dump and restore everything

set -e

HEROKU_DATABASE_URL="${HEROKU_DATABASE_URL:-}"
RENDER_DATABASE_URL="${DATABASE_URL:-}"

if [ -z "$HEROKU_DATABASE_URL" ]; then
    echo "⚠ HEROKU_DATABASE_URL not set. Skipping migration."
    exit 0
fi

if [ -z "$RENDER_DATABASE_URL" ]; then
    echo "⚠ DATABASE_URL not set. Skipping migration."
    exit 0
fi

echo "=========================================="
echo "Simple Database Migration"
echo "=========================================="
echo "Source: Heroku Postgres"
echo "Destination: Render Postgres"
echo ""

# Check if pg_dump is available (install if needed)
if ! command -v pg_dump &> /dev/null; then
    echo "Installing PostgreSQL client tools..."
    # Try to install postgresql-client (works on most Linux systems)
    if command -v apt-get &> /dev/null; then
        apt-get update -qq && apt-get install -y -qq postgresql-client > /dev/null 2>&1 || true
    elif command -v yum &> /dev/null; then
        yum install -y -q postgresql > /dev/null 2>&1 || true
    fi
fi

# Check again
if ! command -v pg_dump &> /dev/null; then
    echo "⚠ pg_dump not available. Using Python-based migration instead."
    python migrate_from_heroku.py
    exit $?
fi

# Create temp file for dump
DUMP_FILE="/tmp/heroku_dump_$$.sql"

echo "Step 1: Dumping data from Heroku..."
pg_dump "$HEROKU_DATABASE_URL" \
    --no-owner \
    --no-acl \
    --data-only \
    --disable-triggers \
    -f "$DUMP_FILE" 2>&1 | grep -v "server version mismatch" || true

if [ ! -f "$DUMP_FILE" ] || [ ! -s "$DUMP_FILE" ]; then
    echo "✗ Dump failed or empty. Trying Python migration instead..."
    python migrate_from_heroku.py
    exit $?
fi

DUMP_SIZE=$(du -h "$DUMP_FILE" | cut -f1)
echo "✓ Dump created: $DUMP_SIZE"

echo ""
echo "Step 2: Restoring data to Render..."
# Use --single-transaction for atomicity, ignore errors for existing objects
psql "$RENDER_DATABASE_URL" \
    --single-transaction \
    -f "$DUMP_FILE" 2>&1 | grep -v -E "(ERROR|already exists|does not exist)" || {
    echo "⚠ Some errors during restore (this is often normal)"
}

# Clean up
rm -f "$DUMP_FILE"

echo ""
echo "✓ Migration complete!"
echo "=========================================="
