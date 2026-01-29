# Fix Wagtail Admin JavaScript Errors

## Errors You're Seeing

1. `webpackJsonp is not defined` - Webpack runtime not loaded
2. `wagtailConfig is not defined` - Wagtail config not available
3. `initDateChooser is not defined` - Date chooser not initialized

## Root Cause

**Wagtail admin JavaScript files aren't loading correctly.** This happens when:
1. Webpack chunk files (`common.js`) aren't collected/uploaded
2. Files are loading in wrong order
3. Static files aren't accessible from S3/WhiteNoise

---

## Solution 1: Verify Files Are Collected (Most Important)

**Check if webpack files exist in S3:**

```bash
# Check if common.js exists
aws s3 ls s3://lcstatic/wagtailadmin/js/common.js

# Check all wagtailadmin JS files
aws s3 ls s3://lcstatic/wagtailadmin/js/ --recursive | grep -E "common|wagtailadmin"
```

**If files are missing:** They weren't collected → Re-run collectstatic

---

## Solution 2: Check Browser Network Tab

1. Open admin page
2. F12 → Network tab → Filter "JS"
3. Look for these files (should load in this order):
   - `common.js` or `common.[hash].js` - **MUST load first** (defines webpackJsonp)
   - `wagtailadmin.js` or `wagtailadmin.[hash].js` - Loads after common.js
   - Other admin JS files

**Check:**
- Are files returning 404?
- Are files loading in wrong order?
- Is `common.js` loading at all?

---

## Solution 3: Re-run collectstatic with --clear

The build script now uses `--clear` flag, but you can manually trigger:

**On Render:**
1. Go to Render Dashboard → Your Service
2. Click "Manual Deploy"
3. Check "Clear build cache"
4. Deploy

This will:
- Clear old static files
- Re-collect all files including webpack chunks
- Upload everything to S3

---

## Solution 4: Check Static File Storage

**Verify which storage backend is being used:**

In `production.py`, check if S3 or WhiteNoise is active:

```python
# If S3 credentials are set → Uses S3
# If not → Uses WhiteNoise
```

**If using S3:**
- Files should be in S3 bucket
- Check: `aws s3 ls s3://lcstatic/wagtailadmin/js/`

**If using WhiteNoise:**
- Files should be in `staticfiles/` directory
- Check: Files are served from app server

---

## Solution 5: Verify collectstatic Output

**Check Render build logs for collectstatic:**

Look for:
```
Collecting static files...
Copying '/opt/render/project/src/.venv/lib/python3.12/site-packages/wagtail/admin/static/wagtailadmin/js/common.js'
...
Post-processing 'wagtailadmin/js/common.js'...
```

**If you don't see these lines:** collectstatic might not be running

**If you see errors:** Fix the errors preventing file collection

---

## Quick Diagnostic

**Check if files are accessible:**

```bash
# On Render (if using S3)
curl -I https://lcstatic.s3.amazonaws.com/wagtailadmin/js/common.js

# On Render (if using WhiteNoise)
curl -I https://localchurches.onrender.com/static/wagtailadmin/js/common.js
```

**If 404:** File doesn't exist → Re-run collectstatic

**If 200:** File exists → Check load order in browser

---

## Most Likely Fix

**The webpack chunk files weren't collected properly.**

**Action:**
1. **Trigger a new deploy on Render** (this runs collectstatic with --clear)
2. **Wait for deploy to complete**
3. **Hard refresh browser** (Ctrl+Shift+R)
4. **Check if errors are gone**

---

## Why This Happens

Wagtail 6.4 uses webpack to bundle JavaScript:
- `common.js` = Webpack runtime (defines `webpackJsonp` and `wagtailConfig`)
- `wagtailadmin.js` = Main admin JS (uses `webpackJsonp`)
- Other JS files depend on both

**If `common.js` doesn't load:**
- `webpackJsonp` is undefined → All webpack-based JS fails
- `wagtailConfig` is undefined → Admin config unavailable
- Date choosers, bulk actions, etc. don't work

---

## After Next Deploy

1. **Check build logs** - Verify collectstatic ran successfully
2. **Verify files in S3** - Check if common.js exists
3. **Test in browser** - Hard refresh and check Network tab
4. **Verify load order** - common.js should load before wagtailadmin.js

---

## If Still Broken After Deploy

**Possible issues:**
1. **Files collected but not uploaded to S3** - Check S3 bucket
2. **Files uploaded but CloudFront cache is stale** - Invalidate CloudFront
3. **Load order issue** - Wagtail should handle this, but check Network tab
4. **Static file storage misconfiguration** - Verify STATICFILES_STORAGE setting

**Next step:** Check the actual error in browser Network tab to see which files are 404.
