# Debug Wagtail Admin CSS Not Loading

## Current Issue

**Wagtail admin CSS/JS files are not being included in the HTML output.**

The admin page HTML only shows:
- Custom CSS: `font-awesome.min.css`, `villareal-turquoise.css`
- **Missing**: Wagtail admin CSS (`wagtailadmin/css/core.css`)
- **Missing**: Wagtail admin JS (`wagtailadmin/js/common.js`, `wagtailadmin.js`)

## Root Cause Analysis

**The admin page HTML shows it's using a custom base template** that only includes custom CSS, not Wagtail admin assets.

**Possible causes:**
1. **Template override** - Custom template is overriding Wagtail admin templates
2. **STATIC_URL not being used** - Wagtail templates aren't picking up S3 STATIC_URL
3. **Template loader order** - Custom templates found before Wagtail templates
4. **S3 file paths** - Files uploaded to wrong location in S3

## Verification Steps

### Step 1: Check What URLs Wagtail Is Generating

**In browser console (F12):**
```javascript
// Check what STATIC_URL Django is using
fetch('/admin/pages/')
  .then(r => r.text())
  .then(html => {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const links = Array.from(doc.querySelectorAll('link[rel="stylesheet"]'));
    console.log('CSS files:', links.map(l => l.href));
  });
```

**Expected:**
- Should see `https://lcstatic.s3.amazonaws.com/wagtailadmin/css/core.css`
- Should see `https://lcstatic.s3.amazonaws.com/wagtailadmin/js/common.js`

**Actual:**
- Only seeing custom CSS files
- No Wagtail admin CSS/JS

### Step 2: Check S3 File Locations

**Verify files exist in S3:**
```bash
# Check if Wagtail admin CSS exists
aws s3 ls s3://lcstatic/wagtailadmin/css/core.css

# Check if Wagtail admin JS exists  
aws s3 ls s3://lcstatic/wagtailadmin/js/common.js

# List all Wagtail admin files
aws s3 ls s3://lcstatic/wagtailadmin/ --recursive | head -20
```

**If files don't exist:**
- `collectstatic` didn't upload them
- Files uploaded to wrong location
- Need to re-run `collectstatic`

### Step 3: Check Template Loading

**Check if custom templates are overriding Wagtail:**
```bash
# Look for Wagtail admin template overrides
find lampstands/core/templates -name "*wagtailadmin*" -o -name "*admin*"
```

**If found:**
- Custom templates may be overriding Wagtail admin templates
- Need to ensure Wagtail admin uses its own templates

### Step 4: Check STATIC_URL in Runtime

**Add debug logging to see what STATIC_URL is:**
```python
# In production.py, add:
import sys
print(f"DEBUG: STATIC_URL = {STATIC_URL}", file=sys.stderr)
print(f"DEBUG: STATICFILES_STORAGE = {STATICFILES_STORAGE}", file=sys.stderr)
```

**Check Render logs** to see what STATIC_URL is actually set to.

## Potential Fixes

### Fix 1: Ensure Files Are Collected to S3 Root

**Added `AWS_LOCATION = ''`** to ensure files are in bucket root, not subdirectory.

**Verify after deploy:**
- Files should be at: `s3://lcstatic/wagtailadmin/css/core.css`
- NOT at: `s3://lcstatic/static/wagtailadmin/css/core.css`

### Fix 2: Check Template Directory Order

**In `TEMPLATES` setting:**
```python
TEMPLATES = [{
    'DIRS': [
        os.path.join(CORE_DIR, 'templates'),  # Custom templates
    ],
    'APP_DIRS': True,  # This should find Wagtail templates
}]
```

**Ensure `APP_DIRS = True`** so Wagtail templates are found.

### Fix 3: Verify collectstatic Output

**Check Render build logs for:**
```
Copying '/opt/render/project/src/.venv/lib/python3.12/site-packages/wagtail/admin/static/wagtailadmin/css/core.css'
...
Post-processing 'wagtailadmin/css/core.css'...
```

**If not present:**
- `collectstatic` isn't finding Wagtail admin files
- Check `STATICFILES_FINDERS` includes `AppDirectoriesFinder`

### Fix 4: Check for Template Overrides

**Wagtail admin should use its own templates:**
- `wagtail/admin/templates/wagtailadmin/base.html`
- Should NOT be overridden by custom templates

**If custom template is overriding:**
- Remove or rename custom template
- Or ensure it extends Wagtail's base template correctly

## Next Steps

1. **Check Render build logs** - Verify collectstatic uploaded Wagtail admin files
2. **Check S3 bucket** - Verify files exist at correct paths
3. **Check browser Network tab** - See what URLs are being requested
4. **Check Render runtime logs** - See what STATIC_URL is set to
5. **Verify template loading** - Ensure Wagtail admin templates are being used

## Most Likely Issue

**Wagtail admin CSS/JS files aren't being included in the HTML at all.**

This suggests:
- Template override preventing Wagtail admin assets from loading
- OR `collectstatic` didn't upload Wagtail admin files to S3
- OR STATIC_URL is wrong and templates can't find files

**Action:** Check build logs and S3 bucket to verify files were collected and uploaded correctly.
