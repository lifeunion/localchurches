# Fix webpackJsonp Loading Order Issue

## The Problem

**Error:** `webpackJsonp is not defined` when loading `wagtailadmin.js`

**Root Cause:** `common.js` (webpack runtime) must load **before** `wagtailadmin.js`, but it's either:
1. Not loading at all
2. Loading after `wagtailadmin.js`

## Why This Happens

Wagtail 6.4 uses webpack to bundle JavaScript:
- `common.js` = Webpack runtime (defines `webpackJsonp` function)
- `wagtailadmin.js` = Main admin JS (uses `webpackJsonp` to load chunks)

**Loading order MUST be:**
1. `common.js` loads first → defines `webpackJsonp`
2. `wagtailadmin.js` loads second → uses `webpackJsonp`

**If order is wrong:**
- `wagtailadmin.js` tries to use `webpackJsonp` → undefined → error

## Current Status

- ✅ `core.css` loads successfully (CSS works)
- ✅ `common.js` exists in S3 (200 OK)
- ✅ `wagtailadmin.js` exists in S3 (200 OK)
- ❌ `common.js` not loading before `wagtailadmin.js`

## Solutions

### Solution 1: Check Browser Network Tab

**In browser (F12 → Network tab):**
1. Filter by "JS"
2. Look for `common.js` and `wagtailadmin.js`
3. Check load order (should be `common.js` first)
4. Check if `common.js` is returning 404 or error

**If `common.js` is 404:**
- File wasn't uploaded to S3
- File path is wrong
- Need to re-run `collectstatic`

**If `common.js` loads after `wagtailadmin.js`:**
- Template issue - scripts in wrong order
- Need to check Wagtail admin template

### Solution 2: Verify Files in S3

**Check if files exist with correct names:**
```bash
# Check common.js
aws s3 ls s3://lcstatic/wagtailadmin/js/common.js

# Check wagtailadmin.js
aws s3 ls s3://lcstatic/wagtailadmin/js/wagtailadmin.js

# List all wagtailadmin JS files
aws s3 ls s3://lcstatic/wagtailadmin/js/ --recursive
```

**If files don't exist:**
- Re-run `collectstatic` on Render
- Check build logs for errors

### Solution 3: Check Template Source

**The HTML should include:**
```html
<script src="https://lcstatic.s3.amazonaws.com/wagtailadmin/js/common.js?v=..."></script>
<script src="https://lcstatic.s3.amazonaws.com/wagtailadmin/js/wagtailadmin.js?v=..."></script>
```

**If missing:**
- Wagtail admin template isn't including these scripts
- May need to check for template overrides
- Or check if STATIC_URL is being used correctly

### Solution 4: Force Script Order (If Needed)

**If scripts are loading in wrong order, you can add a hook:**

```python
# In lampstands/core/wagtail_hooks.py
@hooks.register('insert_global_admin_js')
def ensure_common_js_first():
    """Ensure common.js loads before other Wagtail admin JS"""
    from django.utils.safestring import mark_safe
    from django.conf import settings
    
    # This should already be handled by Wagtail, but if not, we can force it
    # Note: This is a workaround - the real fix is ensuring templates load scripts correctly
    return mark_safe('')
```

**However, this shouldn't be necessary** - Wagtail should handle script order automatically.

## Most Likely Issue

**`common.js` isn't being included in the HTML at all.**

This could be because:
1. Wagtail admin template isn't including it
2. Template override is preventing it
3. STATIC_URL isn't being used correctly in template

## Next Steps

1. **Check browser Network tab** - See if `common.js` is being requested
2. **Check HTML source** - See if `<script>` tags for `common.js` exist
3. **Check Render build logs** - Verify `collectstatic` uploaded `common.js`
4. **Check S3 bucket** - Verify file exists at correct path

## Quick Test

**In browser console, try manually loading common.js:**
```javascript
// Check if common.js can be loaded
fetch('https://lcstatic.s3.amazonaws.com/wagtailadmin/js/common.js')
  .then(r => r.text())
  .then(text => {
    console.log('common.js loaded:', text.substring(0, 100));
    // Check if webpackJsonp is defined
    eval(text);
    console.log('webpackJsonp defined:', typeof webpackJsonp);
  });
```

**If this works:**
- File exists and is accessible
- Issue is with template not including it

**If this fails:**
- File doesn't exist or path is wrong
- Need to re-run `collectstatic`
