# Fix Heroku 500 Error on Admin Page

## Problem
Heroku admin page (`https://www.localchurches.org/testimony-of-Jesus/`) returns 500 error.

## Important Note
**Heroku and Render are separate deployments!** The fixes we've been making are for Render. Heroku might:
- Still have old database schema issues
- Not have the latest code deployed
- Have different environment variables

---

## Step 1: Check Heroku Logs

**Get the actual error from Heroku logs:**

```bash
# Using Heroku CLI
heroku logs --tail --app your-heroku-app-name

# Or check in Heroku Dashboard
# Go to: Heroku Dashboard → Your App → More → View logs
```

**Look for:**
- `ProgrammingError` (database column missing)
- `AttributeError`
- `ImportError`
- Any Python traceback

---

## Step 2: Common Causes

### Cause 1: Missing Database Columns (Most Likely)

Heroku might still have missing Wagtail 6.4 columns:
- `wagtailusers_userprofile.*` columns
- `wagtailcore_workflowstate.*` columns  
- `wagtailcore_taskstate.revision_id`
- `wagtailcore_revision.object_str`

**Fix:** Run the SQL fixes on Heroku database:

```sql
-- Connect to Heroku PostgreSQL and run:
-- (Use the SQL from fix_userprofile_complete.sql)
```

**Or use the API endpoints** (if Heroku has the latest code):
```
https://www.localchurches.org/fix-userprofile/
https://www.localchurches.org/fix-workflowstate/
https://www.localchurches.org/fix-taskstate/
https://www.localchurches.org/fix-revision/
```

### Cause 2: Heroku Hasn't Deployed Latest Code

Heroku might be running old code without our fixes.

**Fix:** Deploy latest code to Heroku:
```bash
git push heroku master
# Or trigger deploy from Heroku Dashboard
```

### Cause 3: Environment Variables Missing

Heroku might be missing required environment variables.

**Check in Heroku Dashboard:**
- Settings → Config Vars
- Verify: `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS`, etc.

### Cause 4: Static Files Not Collected

Wagtail admin CSS/JS might not be in S3.

**Fix:** Run collectstatic on Heroku:
```bash
heroku run python manage.py collectstatic --no-input
```

---

## Step 3: Quick Diagnostic

**Check if it's a database issue:**

1. **Try accessing the fix endpoints:**
   ```
   https://www.localchurches.org/fix-userprofile/
   https://www.localchurches.org/fix-workflowstate/
   https://www.localchurches.org/fix-taskstate/
   https://www.localchurches.org/fix-revision/
   ```

2. **Check Heroku database directly:**
   ```bash
   heroku pg:psql
   # Then run:
   SELECT column_name FROM information_schema.columns 
   WHERE table_name = 'wagtailusers_userprofile' 
   AND column_name IN ('avatar', 'theme', 'dismissibles');
   ```

---

## Step 4: Most Likely Fix

**Heroku probably needs the same database fixes we applied to Render.**

### Option A: Run SQL Manually on Heroku

1. **Connect to Heroku PostgreSQL:**
   ```bash
   heroku pg:psql
   ```

2. **Run the complete fix SQL:**
   ```sql
   -- Copy and paste the SQL from fix_userprofile_complete.sql
   -- This will add all missing columns
   ```

### Option B: Deploy Latest Code to Heroku

If Heroku doesn't have the latest code with our fixes:

```bash
# Make sure you're on the latest code
git pull origin master

# Deploy to Heroku
git push heroku master

# After deploy, the fix commands will run automatically (if build.sh is used)
```

### Option C: Use API Endpoints (If Available)

If Heroku has the latest code with fix endpoints:

```bash
# Visit these URLs in browser (or use curl):
curl https://www.localchurches.org/fix-userprofile/
curl https://www.localchurches.org/fix-workflowstate/
curl https://www.localchurches.org/fix-taskstate/
curl https://www.localchurches.org/fix-revision/
```

---

## Step 5: Check Heroku Build Process

**Verify Heroku is using the same build process:**

Check if Heroku has a `build.sh` or `Procfile` that runs migrations and fixes.

**If not, you might need to:**
1. Add the fix commands to Heroku's build process
2. Or run them manually after deploy

---

## JavaScript Errors (Secondary Issue)

The JavaScript errors you're seeing:
```
ERR_BLOCKED_BY_CLIENT
Uncaught (in promise) Error: Could not establish connection
```

These are usually from:
- **Browser extensions** (ad blockers, privacy tools)
- **Not the cause of the 500 error**

Focus on fixing the 500 error first, then these should resolve.

---

## Quick Action Plan

1. ✅ **Check Heroku logs** - Get the actual error message
2. ✅ **Identify the issue** - Likely missing database columns
3. ✅ **Apply fix** - Run SQL or use API endpoints
4. ✅ **Verify** - Check if admin page loads

---

## Need the Actual Error?

**To get the real error, check Heroku logs:**

```bash
heroku logs --tail --app your-app-name | grep -A 20 "500\|Error\|Traceback"
```

Or check in Heroku Dashboard → Your App → More → View logs

**Share the error message** and I can provide a specific fix!
