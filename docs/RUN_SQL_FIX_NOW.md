# Run SQL Fix NOW - Immediate Solution

## The Problem

Your database is missing these Wagtail 6.4 columns:
- `current_time_zone` ← **This is causing the 500 error right now**
- `preferred_language`
- `rejected_notifications`
- `updated_comments_notifications` (already exists)

## Quick Fix (2 minutes)

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Click on your PostgreSQL database** (`localchurches-db`)
3. **Click "Connect"** → **"psql"** (or copy the External Database URL)
4. **Paste and run this SQL:**

```sql
ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS updated_comments_notifications BOOLEAN DEFAULT FALSE NOT NULL;

ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS rejected_notifications BOOLEAN DEFAULT FALSE NOT NULL;

ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS current_time_zone VARCHAR(40) DEFAULT '' NOT NULL;

ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(10) DEFAULT '' NOT NULL;
```

5. **Verify it worked:**

```sql
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'wagtailusers_userprofile' 
AND column_name IN ('current_time_zone', 'preferred_language', 'rejected_notifications', 'updated_comments_notifications');
```

You should see all 4 columns listed.

6. **Try logging in again** - the admin console should work!

## Why This Happened

When migrating from Heroku, not all Wagtail migrations were applied. Wagtail 6.4 added new fields to the UserProfile model, but your database schema is from an older version.

## After the Fix

Once you run the SQL, the admin console will load correctly. The code has been updated to automatically add these columns in future deployments, so this won't happen again.
