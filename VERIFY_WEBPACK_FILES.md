# Verify Webpack Files Are Collected

## Quick Check

**Verify webpack runtime file exists in S3:**

```bash
# Check if common.js exists
aws s3 ls s3://lcstatic/wagtailadmin/js/common.js

# Or check all wagtailadmin JS files
aws s3 ls s3://lcstatic/wagtailadmin/js/ --recursive | head -20
```

**Expected files:**
- `common.js` or `common.[hash].js` - Webpack runtime (defines webpackJsonp)
- `wagtailadmin.js` or `wagtailadmin.[hash].js` - Main admin JS

---

## Browser Check

1. Open admin page
2. Open Developer Tools (F12) → Network tab
3. Filter by "JS"
4. Look for:
   - `common.js` (or `common.*.js`) - Should load FIRST
   - `wagtailadmin.js` (or `wagtailadmin.*.js`) - Should load AFTER common.js
5. Check if any return 404

**If common.js is 404:** File wasn't collected → Re-run collectstatic

**If both load but in wrong order:** This is a Wagtail template issue (less likely)

---

## Fix: Re-run collectstatic

The build script now uses `--clear` flag to ensure all files are collected properly.

**This will happen automatically on next deploy.**

**Or manually trigger:**
- Render Dashboard → Manual Deploy → "Clear build cache & deploy"
