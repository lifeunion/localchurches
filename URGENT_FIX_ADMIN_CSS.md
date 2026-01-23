# URGENT: Fix Admin CSS Not Loading (404 Error)

## Problem
Wagtail admin CSS files are returning **404 Not Found**, causing the admin page to be completely unstyled.

**Test result:**
```bash
curl -I https://localchurches.onrender.com/static/wagtailadmin/css/core.css
# Returns: HTTP/2 404
```

## Root Cause

**The Wagtail admin CSS files weren't collected or uploaded properly.**

This happens when:
1. `collectstatic` didn't run during deploy
2. `collectstatic` ran but failed silently
3. Files were collected but not uploaded to S3 (if using S3)
4. Files are in wrong location

---

## Immediate Fix

### Step 1: Check Which Storage Render Is Using

**Check Render environment variables:**
- If `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `S3_BUCKET_NAME` are set → **Using S3**
- If not set → **Using WhiteNoise**

### Step 2: Verify Files Exist

**If using S3:**
```bash
aws s3 ls s3://lcstatic/wagtailadmin/css/core.css
```

**If using WhiteNoise:**
- Files should be in `staticfiles/` directory on Render
- Check Render build logs for collectstatic output

### Step 3: Re-run collectstatic

**Option A: Trigger New Deploy (Recommended)**
1. Render Dashboard → Your Service
2. Click "Manual Deploy"
3. Check "Clear build cache"
4. Deploy

**Option B: Check Build Logs**
- Look for "Collecting static files..."
- Look for "Copying wagtailadmin/css/core.css"
- Check for any errors

---

## Quick Diagnostic

**Check what URL the admin page is trying to load:**

1. Open admin page
2. F12 → Network tab
3. Filter "CSS"
4. Look for `core.css` or `core.*.css`
5. Check the URL it's trying to load
6. Check if it returns 404

**Expected URLs:**
- **S3:** `https://lcstatic.s3.amazonaws.com/wagtailadmin/css/core.css`
- **WhiteNoise:** `https://localchurches.onrender.com/static/wagtailadmin/css/core.css`

---

## Most Likely Issue

**collectstatic didn't collect Wagtail admin files properly.**

**Why:**
- Wagtail admin files are in Python package (`site-packages/wagtail/admin/static/`)
- `collectstatic` needs to find and copy them
- If `STATICFILES_FINDERS` is misconfigured, files won't be found

---

## Verify STATICFILES_FINDERS

In `production.py`, should include:
```python
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',  # This finds Wagtail admin files!
    'compressor.finders.CompressorFinder',
)
```

**`AppDirectoriesFinder` is critical** - it finds static files in installed apps (like Wagtail).

---

## Force Re-collection

**Update build.sh to be more verbose:**

```bash
# Collect static files with verbose output
python manage.py collectstatic --no-input --clear --verbosity 2
```

This will show exactly which files are being collected.

---

## If Files Still Missing

**Manually verify Wagtail admin static files exist in package:**

```bash
# On Render (if you have shell access)
ls -la /opt/render/project/src/.venv/lib/python3.12/site-packages/wagtail/admin/static/wagtailadmin/css/core.css
```

If this file exists, `collectstatic` should find it via `AppDirectoriesFinder`.

---

## Temporary Workaround

**If you need admin working NOW:**

1. **Check Render build logs** - See if collectstatic ran
2. **If it didn't run** - Trigger manual deploy
3. **If it ran but failed** - Check error messages
4. **If files are in S3 but 404** - Check S3 permissions/bucket policy

---

## Next Steps

1. **Check Render build logs** for collectstatic output
2. **Verify STATICFILES_FINDERS** includes `AppDirectoriesFinder`
3. **Trigger new deploy** with build cache cleared
4. **Verify files are collected** in build logs
5. **Check if files are accessible** after deploy
