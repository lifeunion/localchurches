# Troubleshooting CloudFront Cache Issues

## Problem: File Still Shows Old Version After Invalidation

If you've created a CloudFront invalidation but still see the old file, try these steps:

---

## Step 1: Verify File Was Actually Uploaded to S3

**Check if the file exists in S3 with the correct content:**

```bash
# Using AWS CLI
aws s3 ls s3://lcstatic/path/to/your/file.css
aws s3 cp s3://lcstatic/path/to/your/file.css - | head -20

# Or check in AWS Console
# Go to: S3 → lcstatic bucket → Navigate to file path
# Download and verify the content
```

**Common issues:**
- File wasn't uploaded (upload failed silently)
- File uploaded to wrong path/location
- File has different name than expected

---

## Step 2: Check Invalidation Status

**Verify invalidation completed:**

```bash
# Using AWS CLI
aws cloudfront get-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --id YOUR_INVALIDATION_ID

# Or check in AWS Console
# CloudFront → Your Distribution → Invalidations tab
# Status should be "Completed" (not "In Progress")
```

**Timeline:**
- Invalidation typically takes **1-5 minutes** to complete
- Can take up to **15 minutes** for global propagation
- Status shows "In Progress" until complete

---

## Step 3: Clear Browser Cache

**The browser itself may be caching the file:**

### Hard Refresh (Most Important!)
- **Chrome/Edge (Windows/Linux):** `Ctrl + Shift + R` or `Ctrl + F5`
- **Chrome/Edge (Mac):** `Cmd + Shift + R`
- **Firefox:** `Ctrl + Shift + R` or `Ctrl + F5`
- **Safari:** `Cmd + Option + R`

### Clear Browser Cache Completely
1. Open Developer Tools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"

### Test in Incognito/Private Mode
- Open a new incognito/private window
- Navigate to your site
- This bypasses browser cache

### Disable Cache in DevTools
1. Open Developer Tools (F12)
2. Go to Network tab
3. Check "Disable cache" checkbox
4. Keep DevTools open while testing

---

## Step 4: Verify You're Using CloudFront URL

**Check which URL your site is actually using:**

### Check HTML Source
```bash
# View page source and check static file URLs
curl -s https://www.localchurches.org | grep -o 'https://[^"]*\.css\|https://[^"]*\.js' | head -10
```

**Look for:**
- `https://lcstatic.s3.amazonaws.com/...` → Direct S3 (no CloudFront)
- `https://d1234567890.cloudfront.net/...` → CloudFront
- `https://cdn.yourdomain.com/...` → Custom CloudFront domain

### Check Django Settings
```python
# In production.py
AWS_S3_CUSTOM_DOMAIN = 'your-cloudfront-domain.cloudfront.net'  # If using CloudFront
# OR
AWS_S3_CUSTOM_DOMAIN = 'lcstatic.s3.amazonaws.com'  # Direct S3 (no CloudFront)
```

**If using direct S3:**
- CloudFront invalidation won't help
- Need to check S3 bucket directly
- May need to configure CloudFront distribution

---

## Step 5: Check for Multiple Distributions

**You might have multiple CloudFront distributions:**

```bash
# List all distributions
aws cloudfront list-distributions \
  --query "DistributionList.Items[*].[Id,DomainName,Origins.Items[0].DomainName]" \
  --output table
```

**Common scenarios:**
- Different distributions for staging/production
- Old distribution still active
- Wrong distribution invalidated

---

## Step 6: Verify File Path is Correct

**The path in your HTML must match the S3 path:**

### Check Actual File Path in Browser
1. Open Developer Tools (F12)
2. Go to Network tab
3. Reload page
4. Find your CSS/JS file
5. Check the **Request URL** - this is the actual path

### Compare with S3
```bash
# List files in S3 directory
aws s3 ls s3://lcstatic/static/css/ --recursive

# Check if your file exists at expected path
aws s3 ls s3://lcstatic/static/css/villareal-turquoise.css
```

**Common issues:**
- File path mismatch (case sensitivity)
- File in different directory
- Different filename than expected

---

## Step 7: Check S3 Object Metadata

**Verify file was uploaded recently:**

```bash
# Check file metadata (last modified date)
aws s3 ls s3://lcstatic/path/to/file.css --recursive

# Get detailed metadata
aws s3api head-object \
  --bucket lcstatic \
  --key path/to/file.css
```

**Look for:**
- `LastModified` - should be recent (when you uploaded)
- `ContentLength` - should match your file size
- `ETag` - should match your file's MD5 hash

---

## Step 8: Force Invalidation with Wildcard

**If specific path didn't work, try directory wildcard:**

```bash
# Invalidate entire directory
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/static/css/*"

# Or invalidate everything (use sparingly!)
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

**Note:** Wildcards count as 1 path, but invalidate all files in that directory.

---

## Step 9: Check CloudFront Cache Behavior

**Verify CloudFront is actually caching (and can be invalidated):**

1. Go to CloudFront Console
2. Select your distribution
3. Go to **Behaviors** tab
4. Check **Cache Policy** settings:
   - Should have caching enabled
   - Min/Max TTL settings
   - Headers that affect caching

**If caching is disabled:**
- Invalidation won't help
- Files served directly from S3
- Check S3 bucket directly

---

## Step 10: Test Direct S3 URL

**Bypass CloudFront to verify S3 has correct file:**

```bash
# Get direct S3 URL
# Format: https://lcstatic.s3.amazonaws.com/path/to/file.css

# Test in browser (add ?v=timestamp to bypass browser cache)
https://lcstatic.s3.amazonaws.com/static/css/villareal-turquoise.css?v=1234567890
```

**If S3 URL shows correct file:**
- Problem is CloudFront cache
- Wait for invalidation to complete
- Or invalidate again

**If S3 URL shows old file:**
- File wasn't uploaded correctly
- Upload file again to S3
- Then invalidate CloudFront

---

## Step 11: Check Django Static Files Collection

**If using `collectstatic`, verify it ran correctly:**

```bash
# Check if collectstatic was run
# Look in Render build logs for:
# "Collecting static files..."
# "Post-processing..."
# "Copying..."

# Verify files were uploaded to S3
aws s3 ls s3://lcstatic/static/ --recursive | grep villareal-turquoise
```

**Common issues:**
- `collectstatic` didn't run
- Files collected to wrong location
- Files not uploaded to S3 after collection

---

## Step 12: Check for CDN/Proxy in Front

**If using Sucuri or other CDN/proxy:**

Your site might be:
1. **Sucuri** → CloudFront → S3
2. **CloudFlare** → CloudFront → S3
3. **Other CDN** → CloudFront → S3

**In this case:**
- Need to clear cache at ALL levels
- Sucuri cache might need clearing separately
- Check Sucuri dashboard for cache purge options

---

## Quick Diagnostic Checklist

- [ ] File exists in S3 with correct content?
- [ ] Invalidation status is "Completed"?
- [ ] Tried hard refresh (Ctrl+Shift+R)?
- [ ] Tested in incognito mode?
- [ ] Verified correct CloudFront distribution?
- [ ] Checked file path matches exactly?
- [ ] File metadata shows recent upload?
- [ ] Direct S3 URL shows correct file?
- [ ] CloudFront cache behavior is enabled?
- [ ] No other CDN/proxy in front?

---

## Most Common Solutions

### Solution 1: Hard Refresh Browser
**90% of issues are browser cache!**
- Press `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac)
- Or use incognito mode

### Solution 2: Wait for Invalidation
**Invalidation takes 1-5 minutes**
- Check invalidation status in CloudFront console
- Wait until status is "Completed"

### Solution 3: Verify File Upload
**File might not have uploaded correctly**
- Check S3 bucket directly
- Verify file content matches your edit
- Re-upload if needed

### Solution 4: Check URL Path
**Path might be wrong**
- Compare browser Network tab URL with S3 path
- Check for case sensitivity issues
- Verify exact path match

---

## Still Not Working?

If none of these work, provide:
1. The exact file path/URL you're checking
2. When you uploaded the file
3. When you created the invalidation
4. What you see in browser vs. what you expect
5. Screenshot of CloudFront invalidation status
