# Static Files Configuration Explanation

## Current Situation

**Both Heroku and Render are using the same S3 bucket (`lcstatic`)** to serve static files. This means:

1. ✅ **Shared static files** - Both environments serve from the same S3 bucket
2. ⚠️ **Conflict risk** - When Render runs `collectstatic` during deployment, it uploads files to S3, which affects Heroku's production site (`www.localchurches.org`)
3. ⚠️ **File changes** - Admin pages and custom CSS/JS files (like `villareal-turquoise.css`) are being overwritten when Render deploys

## What Triggered the Changes?

### 1. **Wagtail 6.4 & Django 5.1 Upgrade** (Commit: `9d249f2`)
   - Upgraded from older Wagtail/Django versions
   - Wagtail 6.4 includes **new admin CSS/JS files** with different hashes/versions
   - When `collectstatic` runs, it uploads these new files to S3

### 2. **Static File Storage Refactoring** (Recent commits)
   - Added WhiteNoise as fallback option
   - Refactored `STORAGES` configuration
   - Changed how static files are collected and served

### 3. **Render Deployment Process**
   - Every Render deploy runs `python manage.py collectstatic` (in `build.sh`)
   - If S3 credentials are set, files are uploaded to S3
   - This overwrites existing files in the shared bucket

## How Static Files Are Currently Configured

### In `production.py` (lines 119-158):

```python
# AWS S3 Settings
AWS_STORAGE_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")

# Conditional logic:
if AWS_STORAGE_BUCKET_NAME and AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    # ✅ USE S3 (if credentials are set)
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
else:
    # ✅ USE WHITENOISE (if S3 credentials are NOT set)
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
    STATIC_URL = '/static/'
```

**Current behavior:**
- **Heroku**: Has S3 credentials → Uses S3 bucket `lcstatic`
- **Render**: Has S3 credentials → Uses S3 bucket `lcstatic` (same bucket!)
- **Result**: Both environments share the same static files

## What Was Used Before?

### Before WhiteNoise:
- **Heroku**: Likely used S3 exclusively via `django-storages`
- **Render**: Was probably configured to use S3 as well (or was added during migration)

### WhiteNoise Introduction:
- WhiteNoise was added as a **fallback option** for Render
- It's designed to serve static files directly from the Django app (no S3 needed)
- Faster, simpler, and cheaper for single-server deployments
- But the code still prefers S3 if credentials are available

## The "villareal-turquoise" Files

These are **custom CSS/JS files** used in your templates:
- `static/css/villareal-turquoise.css` - Custom theme CSS
- `static/js/villareal/jquery*.js` - Custom JavaScript libraries

**Why they're changing:**
- When `collectstatic` runs, it processes ALL static files
- Django Compressor may be minifying/compressing them
- New file hashes are generated (for cache busting)
- Files are uploaded to S3, overwriting old versions

## How to Reconcile the Differences

### Option 1: **Separate S3 Buckets** (Recommended for Production)

**For Heroku (www.localchurches.org):**
- Keep using `lcstatic` bucket
- Don't change anything

**For Render:**
- Create a new S3 bucket: `lcstatic-render` (or similar)
- Update Render environment variables:
  ```
  S3_BUCKET_NAME=lcstatic-render
  ```
- This isolates Render's static files from Heroku

**Pros:**
- ✅ Complete isolation between environments
- ✅ No risk of affecting production
- ✅ Can test static file changes on Render first

**Cons:**
- ⚠️ Need to manage two buckets
- ⚠️ Slightly more complex setup

### Option 2: **Use WhiteNoise on Render Only**

**For Heroku:**
- Keep using S3 (`lcstatic` bucket)
- No changes needed

**For Render:**
- Remove S3 credentials from Render environment variables:
  - Remove `AWS_ACCESS_KEY_ID`
  - Remove `AWS_SECRET_ACCESS_KEY`
  - Remove `S3_BUCKET_NAME`
- Render will automatically fall back to WhiteNoise
- Static files served directly from Render server

**Pros:**
- ✅ Simple - just remove env vars
- ✅ No S3 costs for Render
- ✅ Faster static file serving (no S3 round-trip)
- ✅ Complete isolation from Heroku

**Cons:**
- ⚠️ Static files stored on Render server (disk space)
- ⚠️ Need to run `collectstatic` on every deploy (already doing this)

### Option 3: **Use S3 Path Prefixes** (Advanced)

**For Heroku:**
- Use `lcstatic` bucket, path: `/heroku/`

**For Render:**
- Use `lcstatic` bucket, path: `/render/`

**Pros:**
- ✅ Single bucket, separate paths
- ✅ Easy to manage

**Cons:**
- ⚠️ Requires custom storage backend configuration
- ⚠️ More complex setup

## Recommended Solution

**I recommend Option 2: Use WhiteNoise on Render**

**Why:**
1. Render is designed to work well with WhiteNoise
2. Simpler configuration (just remove S3 env vars)
3. Faster static file serving
4. Complete isolation from Heroku production
5. No additional S3 costs

**Steps:**
1. Go to Render Dashboard → Your Web Service → Environment
2. Remove these environment variables:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `S3_BUCKET_NAME`
3. Redeploy Render service
4. Verify static files are served from `/static/` (not S3)

## Verification

After making changes, verify:

1. **Check Render static files:**
   ```bash
   curl -I https://localchurches.onrender.com/static/wagtailadmin/css/core.css
   # Should return 200, served by WhiteNoise
   ```

2. **Check Heroku static files:**
   ```bash
   curl -I https://www.localchurches.org/static/wagtailadmin/css/core.css
   # Should return 200, served from S3
   ```

3. **Verify they're different:**
   - Render: URL should be `https://localchurches.onrender.com/static/...`
   - Heroku: URL should be `https://lcstatic.s3.amazonaws.com/...`

## Summary

- **Root cause**: Both environments share the same S3 bucket
- **Trigger**: Wagtail 6.4 upgrade + Render deployments running `collectstatic`
- **Impact**: Render deployments overwrite static files used by Heroku production
- **Solution**: Use WhiteNoise on Render, keep S3 on Heroku (Option 2)
