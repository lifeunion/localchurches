# How to Run the Fix on Render

Since I cannot directly access your Render account, here are the steps to run the fix:

## Option 1: Run via Render Shell (Recommended - 2 minutes)

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Navigate to your Web Service** (e.g., `localchurches`)
3. **Click on "Shell"** (in the left sidebar or under "More")
4. **Run this command**:
   ```bash
   python manage.py fix_userprofile
   ```

You should see output like:
```
Fixing wagtailusers_userprofile table...
Adding missing column: updated_comments_notifications
✓ Successfully added column: updated_comments_notifications

✓ Added 1 missing column(s).

✓ Fix completed successfully.
```

## Option 2: Run SQL Directly (Fastest - 30 seconds)

1. **Go to Render Dashboard** → Your **PostgreSQL database**
2. **Click "Connect"** → **"psql"** (or use External Database URL)
3. **Run this SQL**:
   ```sql
   ALTER TABLE wagtailusers_userprofile 
   ADD COLUMN IF NOT EXISTS updated_comments_notifications BOOLEAN DEFAULT FALSE NOT NULL;
   ```

## Option 3: Trigger Automatic Fix (Next Deploy)

The fix will run automatically on your next deployment. To trigger it:

1. **Go to Render Dashboard** → Your **Web Service**
2. **Click "Manual Deploy"** → **"Clear build cache & deploy"**
3. The fix script runs automatically during the build process

## Verification

After running the fix, verify it worked:

1. Visit your site: https://localchurches.onrender.com/testimony-of-Jesus/
2. The error should be gone!

Or check in the database:
```sql
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'wagtailusers_userprofile' 
AND column_name = 'updated_comments_notifications';
```

---

**I recommend Option 1** - it's the easiest and uses the Django management command I created for you.
