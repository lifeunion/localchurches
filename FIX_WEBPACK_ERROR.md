# Fix "webpackJsonp is not defined" Error

## Problem
```
wagtailadmin.js?v=73873709:1 Uncaught ReferenceError: webpackJsonp is not defined
```

## Root Cause
The webpack runtime chunk (`common.js`) isn't loading before `wagtailadmin.js`. This happens when:
1. Static files weren't collected properly
2. Webpack chunk files are missing from S3
3. JavaScript files are loading in wrong order
4. `common.js` file is missing or not accessible

---

## Solution 1: Re-run collectstatic (Most Likely Fix)

The webpack chunk files might not have been uploaded to S3.

**On Render:**
1. Go to Render Dashboard → Your Service
2. Click "Manual Deploy" → "Clear build cache & deploy"
3. This will re-run `collectstatic` and upload all files including webpack chunks

**Or trigger collectstatic manually:**
```bash
# If you have shell access to Render
python manage.py collectstatic --no-input --clear
```

---

## Solution 2: Check if common.js Exists in S3

**Verify the webpack runtime file exists:**
```bash
# Check if common.js is in S3
aws s3 ls s3://lcstatic/wagtailadmin/js/common.js

# Or check all wagtailadmin JS files
aws s3 ls s3://lcstatic/wagtailadmin/js/ --recursive | grep common
```

**If missing, the files weren't collected properly.**

---

## Solution 3: Check Browser Network Tab

1. Open admin page
2. Open Developer Tools (F12) → Network tab
3. Reload page
4. Look for:
   - `common.js` or `common.*.js` - Should load BEFORE wagtailadmin.js
   - `wagtailadmin.js` - Should load AFTER common.js
5. Check if any files return 404

**Expected load order:**
1. `common.js` (or `common.[hash].js`) - Defines webpackJsonp
2. `wagtailadmin.js` (or `wagtailadmin.[hash].js`) - Uses webpackJsonp

---

## Solution 4: Clear Static Files and Re-collect

**If using S3:**
```bash
# Clear old static files (optional, be careful!)
# aws s3 rm s3://lcstatic/wagtailadmin/js/ --recursive

# Re-run collectstatic
python manage.py collectstatic --no-input --clear
```

**If using WhiteNoise:**
```bash
# Clear staticfiles directory
rm -rf staticfiles/

# Re-collect
python manage.py collectstatic --no-input
```

---

## Solution 5: Check Static File Storage Configuration

**Verify STATICFILES_STORAGE is correct:**

In `production.py`, if using S3:
```python
STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
```

If using WhiteNoise:
```python
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
```

**Issue:** If using `CompressedManifestStaticFilesStorage` with S3, it might cause issues with webpack chunks.

---

## Solution 6: Verify collectstatic Ran Successfully

**Check Render build logs:**
- Look for: "Collecting static files..."
- Look for: "Copying..." or "Post-processing..."
- Check for any errors during collection

**If collectstatic failed or was skipped:**
- Files won't be in S3
- Admin JS won't work

---

## Quick Diagnostic

**Check if common.js is accessible:**
```bash
# On Render
curl -I https://localchurches.onrender.com/static/wagtailadmin/js/common.js

# Or if using S3
curl -I https://lcstatic.s3.amazonaws.com/wagtailadmin/js/common.js
```

**If 404:** File wasn't collected → Re-run collectstatic

**If 200:** File exists → Check load order in browser Network tab

---

## Most Likely Fix

**Re-run collectstatic on Render:**

1. **Trigger a new deploy** (this runs collectstatic automatically)
2. **Or manually run** (if you have shell access):
   ```bash
   python manage.py collectstatic --no-input --clear
   ```

This will ensure all Wagtail admin JS files, including webpack chunks, are collected and uploaded.

---

## Why This Happens

Wagtail 6.4 uses webpack to bundle JavaScript:
- `common.js` = Webpack runtime (defines `webpackJsonp`)
- `wagtailadmin.js` = Main admin JS (uses `webpackJsonp`)

If `common.js` doesn't load first, `wagtailadmin.js` fails with "webpackJsonp is not defined".

**Common causes:**
- `collectstatic` didn't run during deploy
- Files weren't uploaded to S3
- Files were uploaded but in wrong order
- Browser cache serving old/broken files

---

## After Fixing

1. **Hard refresh browser** (Ctrl+Shift+R or Cmd+Shift+R)
2. **Clear browser cache** completely
3. **Test in incognito mode**
4. **Verify:** Admin page should load without JavaScript errors
