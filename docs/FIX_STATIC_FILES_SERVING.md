# Fix Static Files Serving (CSS and JavaScript 404 Errors)

## Problem

**Both CSS and JavaScript files are returning 404 errors:**
- CSS: `/static/wagtailadmin/css/core.css` → 404
- JS: `/static/wagtailadmin/js/common.js` → 404

**But files exist in S3:**
- `https://lcstatic.s3.amazonaws.com/wagtailadmin/css/core.css` → 200 OK
- `https://lcstatic.s3.amazonaws.com/wagtailadmin/js/common.js` → 200 OK

---

## Root Cause

**Render is using WhiteNoise (no S3 credentials), but files are in S3, not locally.**

When Render doesn't have S3 credentials:
- `STATIC_URL = '/static/'` (WhiteNoise)
- Files must be in local `staticfiles/` directory
- WhiteNoise serves files from local directory

**But currently:**
- Files are in S3 (from previous deploys or Heroku)
- Files are NOT in local `staticfiles/` directory
- WhiteNoise can't serve files that don't exist locally → 404

---

## Solution Options

### Option 1: Set S3 Credentials on Render (Recommended)

**If you want to use S3 for static files:**

1. **Render Dashboard** → Your Service → Environment
2. **Add these environment variables:**
   - `AWS_ACCESS_KEY_ID` = Your AWS access key
   - `AWS_SECRET_ACCESS_KEY` = Your AWS secret key
   - `S3_BUCKET_NAME` = `lcstatic`

3. **Redeploy** - Render will now use S3 storage

**Benefits:**
- Files already exist in S3
- No need to re-collect files
- Works immediately

---

### Option 2: Collect Files Locally for WhiteNoise

**If you want to use WhiteNoise (no S3):**

The build script already collects files locally, but you need to verify:

1. **Check Render build logs** - Look for:
   ```
   Collecting static files...
   Copying 'wagtailadmin/css/core.css'
   Copying 'wagtailadmin/js/common.js'
   ```

2. **Verify files are collected** - Build script now checks this

3. **Ensure WhiteNoise middleware is active** - Should be in `MIDDLEWARE`

**If files aren't being collected:**
- Check `STATICFILES_FINDERS` includes `AppDirectoriesFinder`
- Check for errors in collectstatic output
- Verify `STATIC_ROOT` is correct

---

## Current Configuration

**In `production.py`:**

```python
# If S3 credentials are set → Uses S3
if AWS_STORAGE_BUCKET_NAME and AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
else:
    # Uses WhiteNoise
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
    STATIC_URL = '/static/'
```

**Check which one is active:**
- Look at Render build logs for "DEBUG: Using WhiteNoise" or "Using S3"
- Or check Render environment variables

---

## Immediate Fix

### Step 1: Check Render Environment Variables

**Render Dashboard** → Your Service → Environment

**Do you see:**
- `AWS_ACCESS_KEY_ID`?
- `AWS_SECRET_ACCESS_KEY`?
- `S3_BUCKET_NAME`?

**If YES:** Render should use S3 → Check why it's not working
**If NO:** Render uses WhiteNoise → Files must be collected locally

---

### Step 2: Check Build Logs

**Look for collectstatic output:**
```
Collecting static files...
✅ Wagtail admin CSS found: /opt/render/project/src/staticfiles/wagtailadmin/css/core.css
```

**If you see "❌ Wagtail admin CSS NOT found":**
- Files weren't collected → Check collectstatic errors
- Fix the errors and redeploy

---

### Step 3: Choose Your Solution

**Option A: Use S3 (Easiest)**
1. Add S3 credentials to Render
2. Redeploy
3. Files will load from S3

**Option B: Use WhiteNoise**
1. Ensure collectstatic runs successfully
2. Verify files are in `staticfiles/` directory
3. Ensure WhiteNoise middleware is active
4. Files will load from local directory

---

## Why This Happens

**During Heroku to Render migration:**
- Heroku was using S3 → Files uploaded to S3
- Render doesn't have S3 credentials → Uses WhiteNoise
- WhiteNoise needs local files → Files not collected locally
- Result: 404 errors

**The fix:**
- Either set S3 credentials on Render (use existing S3 files)
- Or ensure files are collected locally (use WhiteNoise)

---

## Verification After Fix

**Test CSS:**
```bash
curl -I https://localchurches.onrender.com/static/wagtailadmin/css/core.css
# Should return 200 OK
```

**Test JS:**
```bash
curl -I https://localchurches.onrender.com/static/wagtailadmin/js/common.js
# Should return 200 OK
```

**In browser:**
- Open admin page
- F12 → Network tab
- Check CSS and JS files load (200 OK, not 404)

---

## Next Steps

1. **Check Render environment variables** - Do you have S3 credentials?
2. **If YES:** Verify S3 is being used (check build logs)
3. **If NO:** Verify files are collected locally (check build logs)
4. **Redeploy if needed** - After fixing configuration
5. **Test in browser** - Hard refresh and check Network tab
