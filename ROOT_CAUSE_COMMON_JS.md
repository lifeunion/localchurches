# Root Cause: common.js Not Being Requested

## The Problem

**`common.js` is not being requested by the browser** - it's not in the HTML at all.

**Current HTML only shows:**
- Custom JS: `jquery.min.js`, `bootstrap.min.js`, `owl.carousel.min.js`
- **Missing**: `common.js` (webpack runtime)
- **Missing**: `wagtailadmin.js` (main admin JS)

## Root Cause

**The admin page is using a custom template that doesn't include Wagtail admin JavaScript.**

The HTML shows it's using `lampstands/core/templates/lampstands/base.html`, which only includes custom JavaScript files, NOT Wagtail admin JavaScript files.

**Wagtail admin should use its own templates** (`wagtail/admin/templates/wagtailadmin/base.html`) which include:
- `common.js` (webpack runtime)
- `wagtailadmin.js` (main admin JS)
- Other Wagtail admin JS files

## Why This Happens

**Template loading order issue:**
1. Django finds custom templates first (`lampstands/core/templates/`)
2. Custom `base.html` is used instead of Wagtail's base template
3. Custom template doesn't include Wagtail admin scripts
4. Result: `common.js` never loads → `webpackJsonp is not defined`

## The Fix

**Option 1: Ensure Wagtail Admin Uses Its Own Templates (Recommended)**

Wagtail admin should automatically use its own templates. If it's not, check:

1. **Template directory order** - Custom templates shouldn't override Wagtail admin templates
2. **No template override** - Ensure no custom template is named `wagtailadmin/base.html`
3. **Template inheritance** - If customizing, extend Wagtail's base, don't replace it

**Option 2: Check for Template Override**

Look for any custom Wagtail admin template overrides:
```bash
find lampstands/core/templates -name "*wagtailadmin*" -o -name "*admin*base*"
```

**If found:**
- Remove or rename custom override
- Let Wagtail use its default templates

**Option 3: Verify Template Loading**

Check `TEMPLATES` setting:
```python
TEMPLATES = [{
    'DIRS': [
        os.path.join(CORE_DIR, 'templates'),  # Custom templates
    ],
    'APP_DIRS': True,  # Must be True to find Wagtail templates
}]
```

**`APP_DIRS = True` is critical** - this allows Django to find Wagtail's templates.

## Verification

**Check what template is actually being used:**

1. **View page source** (Ctrl+U)
2. **Look for template comments** or unique identifiers
3. **Check if it extends Wagtail's base** or uses custom base

**Expected (Wagtail admin template):**
```html
<!-- Should see Wagtail admin structure -->
<div id="wagtail">
  <!-- Wagtail admin content -->
</div>
```

**Actual (Custom template):**
```html
<!-- Custom template structure -->
<div class="page-wrapper">
  <div class="header-wrapper">
    <!-- Custom header -->
  </div>
</div>
```

## Most Likely Solution

**The admin page is incorrectly using the custom `base.html` template.**

**Fix:**
1. Ensure Wagtail admin URLs use Wagtail's own templates
2. Check if there's a template override in `lampstands/core/templates/wagtailadmin/`
3. Verify `APP_DIRS = True` in TEMPLATES setting
4. Check if custom template is somehow being used for admin pages

## Next Steps

1. **Check for template overrides** - Look for any `wagtailadmin` templates in custom directory
2. **Verify TEMPLATES setting** - Ensure `APP_DIRS = True`
3. **Check URL configuration** - Ensure admin URLs are correctly configured
4. **Test with minimal template** - Temporarily remove custom templates to see if Wagtail admin works

---

## Investigation (Jan 2025) & Fix Applied

### What We Checked

1. **Template overrides**  
   - No `lampstands/core/templates/wagtailadmin/` override existed.  
   - Wagtail admin was using its default `wagtailadmin/admin_base.html` from the package.

2. **TEMPLATES**  
   - `APP_DIRS = True` ✓  
   - `DIRS = [lampstands/core/templates]` — checked first, then app dirs.  
   - No `wagtailadmin/base.html` or `wagtailadmin/admin_base.html` in `lampstands/core/templates/` before the fix.

3. **URLs**  
   - Wagtail admin at `testimony-of-Jesus/` via `wagtailadmin_urls` ✓  

4. **Wagtail 6.4 `admin_base.html`**  
   - In Wagtail 6.4, `wagtailadmin/admin_base.html` does **not** include `common.js`.  
   - It includes: `core.js`, `vendor.js`, `wagtailadmin.js`, etc.  
   - In this project, `wagtailadmin.js` calls `webpackJsonp(...)`; only `common.js` defines `window.webpackJsonp`.  
   - So with the default template, `common.js` is never loaded → `webpackJsonp is not defined` when `wagtailadmin.js` runs.

5. **Static files**  
   - `common.js` and `wagtailadmin.js` are present under `static/wagtailadmin/js/`.  
   - Problem was **only** that `common.js` was not referenced in the admin HTML.

### Root Cause (confirmed)

**Wagtail 6.4’s default `wagtailadmin/admin_base.html` does not include `common.js`.**  
For a webpack-built `wagtailadmin.js` that uses `webpackJsonp`, the webpack runtime (`common.js`) must be loaded before it. Because it was never included, `common.js` was not requested and `webpackJsonp is not defined` occurred.

### Fix Applied

A **custom** `wagtailadmin/admin_base.html` was added so the admin includes `common.js` **before** `wagtailadmin.js`:

- **File:** `lampstands/core/templates/wagtailadmin/admin_base.html`
- **Change:** Copy of Wagtail 6.4’s `admin_base.html` with one extra line in the `{% block js %}` block:
  - `<script src="{% versioned_static 'wagtailadmin/js/common.js' %}"></script>`  
  - Inserted **after** `vendor.js` and **before** `wagtailadmin.js`.

Load order is now: … → `core.js` → `vendor.js` → **`common.js`** → `wagtailadmin.js` → …, so `webpackJsonp` exists when `wagtailadmin.js` runs.

### Verification

1. Open Wagtail admin (e.g. `/testimony-of-Jesus/`).
2. View page source (Ctrl+U / Cmd+U) and confirm a `<script src=".../wagtailadmin/js/common.js...">` tag appears **before** `wagtailadmin.js`.
3. In the Network tab, confirm `common.js` is requested and returns 200.
4. In the console, `webpackJsonp is not defined` should no longer appear.
