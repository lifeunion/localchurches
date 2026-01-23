# Fix WhiteNoise and S3 Conflict

## The Problem

**WhiteNoise middleware was intercepting `/static/` URLs even when S3 is configured.**

When S3 is configured:
- `STATIC_URL = 'https://lcstatic.s3.amazonaws.com/'`
- Wagtail admin templates use `{% static %}` tag → generates S3 URLs
- But if any code generates `/static/` URLs, WhiteNoise intercepts them
- WhiteNoise tries to serve from local filesystem → 404 (files are in S3)

---

## The Fix

**Removed WhiteNoise middleware when S3 is configured.**

In `production.py`, when S3 credentials are detected:
```python
if 'whitenoise.middleware.WhiteNoiseMiddleware' in MIDDLEWARE:
    MIDDLEWARE = [m for m in MIDDLEWARE if m != 'whitenoise.middleware.WhiteNoiseMiddleware']
```

This ensures:
- ✅ S3 URLs work correctly
- ✅ No conflicts between WhiteNoise and S3
- ✅ Static files load from S3 as expected

---

## Why This Happens

**WhiteNoise middleware:**
- Intercepts requests to `/static/*` paths
- Serves files from local `STATIC_ROOT` directory
- Returns 404 if files don't exist locally

**When using S3:**
- Files are in S3, not locally
- URLs should be `https://lcstatic.s3.amazonaws.com/...`
- But if any code generates `/static/...` URLs, WhiteNoise intercepts → 404

**Solution:**
- Remove WhiteNoise when S3 is configured
- WhiteNoise is only needed when serving files locally

---

## Verification

After deploy, check:

1. **Build logs should show:**
   ```
   DEBUG: ✅ Removed WhiteNoise middleware (using S3 for static files)
   ```

2. **Browser Network tab:**
   - CSS/JS files should load from `https://lcstatic.s3.amazonaws.com/...`
   - Should NOT be `/static/...` URLs
   - Should return 200 OK (not 404)

3. **Admin page should:**
   - Load CSS correctly (no broken styling)
   - Load JavaScript correctly (no `webpackJsonp is not defined` errors)
   - All static files accessible

---

## If Still Broken

**Check if Wagtail admin is generating correct URLs:**

1. **View page source** (Ctrl+U)
2. **Search for** `wagtailadmin` or `core.css`
3. **Check the URL:**
   - ✅ Should be: `https://lcstatic.s3.amazonaws.com/wagtailadmin/css/core.css`
   - ❌ Should NOT be: `/static/wagtailadmin/css/core.css`

**If URLs are wrong:**
- Check `STATIC_URL` setting is correct
- Verify Wagtail templates use `{% static %}` tag (not hardcoded paths)
- Check for any URL overrides in templates or hooks

---

## Next Steps

1. **Wait for deploy to complete**
2. **Hard refresh browser** (Ctrl+Shift+R)
3. **Check admin page** - CSS and JS should load correctly
4. **Verify in Network tab** - All files should return 200 OK from S3
