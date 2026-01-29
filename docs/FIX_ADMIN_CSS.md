# Fix Wagtail Admin CSS Issues

## Problem
Admin page CSS is broken - layout is all over the place, unreadable.

## Possible Causes

### 1. Custom CSS Interfering
The `fix_admin_login_css` hook might be affecting the main admin interface.

**Fixed:** CSS is now scoped to `body.login` to only affect login page.

### 2. Wagtail Admin CSS Files Not Loading
The Wagtail admin CSS files might not be available from S3/static files.

**Check:**
```bash
# Check if Wagtail admin CSS exists in S3
aws s3 ls s3://lcstatic/wagtailadmin/css/ --recursive | grep core.css

# Or check on Render
curl -I https://localchurches.onrender.com/static/wagtailadmin/css/core.css
```

### 3. FontAwesome Path Issue
The FontAwesome CSS link might be broken.

**Current path:** `lampstands/vendor/fontawesome/css/font-awesome.min.css`

**Check if file exists:**
```bash
ls -la static/lampstands/vendor/fontawesome/css/font-awesome.min.css
```

### 4. Static Files Not Collected
Wagtail admin CSS might not have been collected to S3.

**Solution:** Run `collectstatic` on Render (should happen automatically during deploy).

---

## Quick Fixes

### Option 1: Temporarily Disable Custom CSS Hooks

Comment out the CSS hooks in `wagtail_hooks.py`:

```python
# Temporarily disabled to fix admin CSS
# @hooks.register('insert_global_admin_css')
# def import_fontawesome_stylesheet():
#     ...

# @hooks.register('insert_global_admin_css')
# def fix_admin_login_css():
#     ...
```

### Option 2: Check Browser Console

1. Open admin page
2. Open Developer Tools (F12)
3. Go to Console tab
4. Look for CSS loading errors
5. Go to Network tab
6. Check which CSS files are failing to load (404 errors)

### Option 3: Verify Static Files Are Served

Check if Wagtail admin CSS is accessible:

```bash
# On Render
curl -I https://localchurches.onrender.com/static/wagtailadmin/css/core.css

# Should return 200 OK
```

If 404, the files weren't collected to S3/staticfiles.

---

## Most Likely Issue

**Wagtail admin CSS files are missing or not loading from S3.**

This can happen if:
- `collectstatic` didn't run during deploy
- Files weren't uploaded to S3
- S3 bucket path is wrong
- CloudFront cache is serving old/broken files

---

## Immediate Action

1. **Check browser console** for CSS loading errors
2. **Check Network tab** to see which CSS files are 404
3. **Verify Wagtail admin CSS exists in S3:**
   ```bash
   aws s3 ls s3://lcstatic/wagtailadmin/css/core.css
   ```
4. **If missing, trigger collectstatic on Render:**
   - Go to Render dashboard
   - Manual deploy or wait for next auto-deploy
   - Check build logs for `collectstatic` output

---

## If CSS Files Are Missing

**Re-run collectstatic:**

```bash
# On Render (via shell or build script)
python manage.py collectstatic --no-input
```

This will upload all Wagtail admin CSS files to S3.
