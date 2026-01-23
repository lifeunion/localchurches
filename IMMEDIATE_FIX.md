# Immediate Fix for Wagtail Admin Console Issue

## Root Cause

The database is missing multiple columns that Wagtail 6.4 expects in the `wagtailusers_userprofile` table:
- `current_time_zone` (causing the current 500 error)
- `preferred_language` 
- `rejected_notifications`
- `updated_comments_notifications` (already added)

When you log in, Wagtail tries to load your user profile and queries these columns, causing a 500 error. The error handler then shows the 500.html template (with header/footer), which is why you see a blank page.

## Immediate Fix (Run This Now)

1. **Go to Render Dashboard** → Your PostgreSQL database (`localchurches-db`)
2. **Click "Connect"** → **"psql"** (or use External Database URL)
3. **Run this SQL:**

```sql
-- Add all missing Wagtail 6.4 UserProfile columns
ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS updated_comments_notifications BOOLEAN DEFAULT FALSE NOT NULL;

ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS rejected_notifications BOOLEAN DEFAULT FALSE NOT NULL;

ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS current_time_zone VARCHAR(40) DEFAULT '' NOT NULL;

ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(10) DEFAULT '' NOT NULL;
```

4. **Verify the columns were added:**

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'wagtailusers_userprofile' 
AND column_name IN ('updated_comments_notifications', 'rejected_notifications', 'current_time_zone', 'preferred_language')
ORDER BY column_name;
```

5. **Try logging in again** - the admin console should now work!

## Alternative: Wait for Auto-Fix

The code has been updated to automatically fix these columns on the next deploy. Once the deploy completes (2-3 minutes), you can also call:

```
https://localchurches.onrender.com/fix-userprofile/
```

This will add all missing columns automatically.

## CSS Issue (Bird Icon)

The CSS issue with the bird icon being too big is likely a static file caching issue. After fixing the database columns:
1. Hard refresh your browser (Cmd+Shift+R or Ctrl+Shift+R)
2. Clear browser cache
3. The CSS should load correctly

If it persists, it might be an S3 static file issue - check that Wagtail admin CSS files are being served correctly from S3.
