# Quick Fix for Missing UserProfile Column

The error `column wagtailusers_userprofile.updated_comments_notifications does not exist` indicates that your database is missing a column that Wagtail 6.4 expects.

## Option 1: Run the Fix Script (Recommended)

The `fix_wagtail_userprofile.py` script has been added to your project and will run automatically during builds. However, to fix it immediately:

### On Render (via Shell):

1. Go to your Render dashboard → Web Service → **Shell**
2. Run:
```bash
python fix_wagtail_userprofile.py
```

### Or via Render Console:

1. Go to Render dashboard → Web Service → **Events** → **Manual Deploy** → **Clear build cache & deploy**
2. This will trigger a new build that runs the fix script automatically

## Option 2: Run SQL Directly (Fastest)

If you have direct database access:

1. Go to Render dashboard → Your PostgreSQL database → **Connect** → **psql**
2. Or use the External Database URL with `psql` from your machine
3. Run:

```sql
-- Check if column exists
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'wagtailusers_userprofile' 
AND column_name = 'updated_comments_notifications';

-- If the query returns nothing, add the column:
ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS updated_comments_notifications BOOLEAN DEFAULT FALSE NOT NULL;
```

## Option 3: Run All Wagtail Migrations

Sometimes the issue is that Wagtail migrations weren't fully applied:

```bash
# In Render Shell or locally
python manage.py migrate wagtailusers
python manage.py migrate
```

## Verification

After running the fix, verify the column exists:

```sql
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'wagtailusers_userprofile' 
AND column_name = 'updated_comments_notifications';
```

You should see:
- `column_name`: `updated_comments_notifications`
- `data_type`: `boolean`
- `column_default`: `false`

## Why This Happened

This typically occurs when:
1. Database was migrated from an older Wagtail version
2. Not all Wagtail migrations were applied during migration
3. The database schema is out of sync with Wagtail 6.4

## Prevention

The `build.sh` script has been updated to automatically run `fix_wagtail_userprofile.py` after migrations, so future deployments should prevent this issue.
