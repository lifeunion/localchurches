# Database Migration: Heroku Postgres → Render Postgres

## Overview
This guide will help you migrate your database from Heroku Postgres to Render Postgres.

## Prerequisites
- PostgreSQL client tools installed (`pg_dump` and `psql`)
- Access to your Heroku Postgres database
- Render Postgres database created (already done: `localchurches-db`)

## Step 1: Get Connection Strings

### Heroku Postgres Connection String
Run this command to get your Heroku database URL:
```bash
heroku pg:credentials:url DATABASE_URL
```

Or get it from Heroku dashboard → Your App → Settings → Config Vars → `DATABASE_URL`

### Render Postgres Connection String
1. Go to Render dashboard: https://dashboard.render.com/d/dpg-d5ojhtc9c44c738ni630-a
2. Click on "Connection Info" or "Info" tab
3. Copy the "Internal Database URL" or "External Connection String"
   - Format: `postgresql://user:password@host:port/database`

## Step 2: Link Database to Web Service (Recommended)

**Before migrating, link the database to your web service:**

1. Go to: https://dashboard.render.com/web/srv-d5ntupuid0rc73cieeg0
2. Navigate to "Environment" section
3. Click "Link Database" or "Add Database"
4. Select "localchurches-db"
5. This automatically sets the `DATABASE_URL` environment variable

**Note:** After linking, your app will use the Render database. Make sure to migrate data first!

## Step 3: Migrate Data

### Option A: Using the Migration Script (Recommended)

1. Set environment variables:
```bash
# Get Heroku connection string: heroku pg:credentials:url DATABASE_URL
export HEROKU_DATABASE_URL="postgresql://user:password@host:port/database"

# Get Render connection string from Render dashboard -> localchurches-db -> Connection Info
export RENDER_DATABASE_URL="postgresql://user:password@host:port/database"
```

2. Run the migration script:
```bash
./migrate_database.sh
```

### Option B: Manual Migration

1. **Dump data from Heroku:**
```bash
pg_dump "$HEROKU_DATABASE_URL" \
  --verbose --clean --no-acl --no-owner \
  -f heroku_backup.sql
```

   Or get the connection string from Heroku:
   ```bash
   heroku pg:credentials:url DATABASE_URL
   ```

2. **Restore to Render:**
```bash
psql "YOUR_RENDER_DATABASE_URL" -f heroku_backup.sql
```

Replace `YOUR_RENDER_DATABASE_URL` with the connection string from Render dashboard.

## Step 4: Verify Migration

After migration, verify the data:

1. Check table counts match
2. Test your application
3. Verify critical data is present

## Step 5: Update Application

Once migration is complete and database is linked:

1. The `DATABASE_URL` environment variable will be automatically set by Render
2. Your next deployment will use the new database
3. Migrations will run automatically during build

## Troubleshooting

### Connection Issues
- Ensure your IP is allowed (for external connections)
- Use the "Internal Database URL" if running from Render services
- Check firewall settings

### Migration Errors
- Some errors during restore are normal (e.g., if tables already exist)
- Check the backup file was created successfully
- Verify connection strings are correct

### Missing Data
- Check the backup file size (should be > 0)
- Verify all tables were included in the dump
- Check migration logs for errors

## Important Notes

⚠️ **Free Plan Expiration:** The free Postgres plan expires on **February 20, 2026**. Consider upgrading to a paid plan for production use.

⚠️ **Backup First:** Always keep a backup of your Heroku database before migration.

⚠️ **Test First:** Test the migration on a staging environment if possible.
