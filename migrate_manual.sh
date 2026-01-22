#!/usr/bin/env bash
# =============================================================================
# MANUAL DATABASE MIGRATION — Run this on your Mac/laptop, NOT on Render.
# =============================================================================
# Render's build servers cannot reach Heroku Postgres, so migration during
# deploy never works. This script dumps from Heroku and restores to Render
# using your machine (which can reach both).
#
# Prerequisites:
#   - PostgreSQL client tools: brew install libpq && brew link --force libpq
#   - HEROKU_DATABASE_URL and RENDER_DATABASE_URL set (see below)
#
# Usage:
#   export HEROKU_DATABASE_URL='postgres://...'   # From Heroku config
#   export RENDER_DATABASE_URL='postgresql://...' # Render → DB → External URL
#   ./migrate_manual.sh
# =============================================================================

set -e

HEROKU="${HEROKU_DATABASE_URL:-}"
RENDER="${RENDER_DATABASE_URL:-}"

if [ -z "$HEROKU" ]; then
  echo "Error: HEROKU_DATABASE_URL is not set."
  echo "  Get it: Heroku Dashboard → App → Settings → Reveal Config Vars → DATABASE_URL"
  echo "  Or:     heroku config:get DATABASE_URL -a YOUR_APP"
  exit 1
fi

if [ -z "$RENDER" ]; then
  echo "Error: RENDER_DATABASE_URL is not set."
  echo "  Get it: Render Dashboard → Your Postgres service → Connect → External"
  echo "  Use the 'External Database URL' (not Internal)."
  echo "  If needed, add your IP in the database's 'Networking' / 'Allow IP' section."
  exit 1
fi

if ! command -v pg_dump >/dev/null 2>&1 || ! command -v psql >/dev/null 2>&1; then
  echo "Error: pg_dump and psql are required."
  echo "  macOS: brew install libpq && brew link --force libpq"
  echo "  Ubuntu: sudo apt-get install postgresql-client"
  exit 1
fi

DUMP="/tmp/heroku_to_render_dump_$$.sql"
echo "=============================================="
echo "Manual migration: Heroku → Render"
echo "=============================================="
echo ""

echo "1. Full dump from Heroku (schema + data)..."
pg_dump "$HEROKU" --no-owner --no-acl --format=plain -f "$DUMP"

if [ ! -s "$DUMP" ]; then
  echo "Error: Dump file is empty. Check HEROKU_DATABASE_URL and connectivity."
  rm -f "$DUMP"
  exit 1
fi

echo "   Done. Size: $(du -h "$DUMP" | cut -f1)"
echo ""

echo "2. Wipe Render DB (drop public schema, recreate)..."
echo "   WARNING: This deletes ALL data in the Render database."
read -r -p "   Continue? [y/N] " response
if [[ ! "$response" =~ ^[yY]$ ]]; then
  echo "   Aborted. Dump kept at $DUMP"
  exit 0
fi
psql "$RENDER" -v ON_ERROR_STOP=1 -c "
  DROP SCHEMA public CASCADE;
  CREATE SCHEMA public;
  GRANT ALL ON SCHEMA public TO public;
"
echo "   Done."
echo ""

echo "3. Restore Heroku dump into Render..."
psql "$RENDER" -v ON_ERROR_STOP=1 -f "$DUMP"

rm -f "$DUMP"
echo ""
echo "=============================================="
echo "Migration finished."
echo "=============================================="
echo "Next:"
echo "  1. Redeploy your Render web service (or trigger a deploy)."
echo "  2. Open https://localchurches.onrender.com/diagnostic/ to verify."
echo "  3. Remove HEROKU_DATABASE_URL from Render env if you no longer need it."
echo ""
