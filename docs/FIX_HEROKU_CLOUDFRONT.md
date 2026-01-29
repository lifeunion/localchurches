# Fix Heroku CloudFront Cache - Quick Guide

## ✅ Found Your CloudFront Setup

**Heroku is using CloudFront:**
- **CloudFront Domain:** `d24pmr7604s8mt.cloudfront.net`
- **Static Files URL:** `https://d24pmr7604s8mt.cloudfront.net/css/villareal-turquoise.css`

## The Problem

- **Render:** Uploaded new file to S3 ✅
- **Heroku CloudFront:** Still serving cached file from 17 hours ago ❌
- **Solution:** Invalidate CloudFront cache

---

## Step 1: Find Distribution ID

### Option A: AWS Console (Easiest)

1. Go to: https://console.aws.amazon.com/cloudfront/
2. Look for distribution with domain: `d24pmr7604s8mt.cloudfront.net`
3. Copy the **Distribution ID** (starts with `E`, e.g., `E1234567890ABC`)

### Option B: AWS CLI (After configuring)

```bash
# List all distributions and find the one with this domain
aws cloudfront list-distributions \
  --query "DistributionList.Items[?DomainName=='d24pmr7604s8mt.cloudfront.net'].[Id,DomainName,Status]" \
  --output table
```

---

## Step 2: Invalidate CloudFront Cache

### Using AWS Console (Recommended)

1. Go to: https://console.aws.amazon.com/cloudfront/
2. Click the distribution (with domain `d24pmr7604s8mt.cloudfront.net`)
3. Click **"Invalidations"** tab
4. Click **"Create invalidation"**
5. Enter path: `/css/villareal-turquoise.css`
   - Or use `/css/*` to invalidate all CSS files
6. Click **"Create invalidation"**
7. Wait 1-5 minutes for propagation

### Using AWS CLI (After configuring)

```bash
# Replace YOUR_DISTRIBUTION_ID with the ID from Step 1
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/css/villareal-turquoise.css"
```

### Using Python Script

```bash
export CLOUDFRONT_DISTRIBUTION_ID=YOUR_DISTRIBUTION_ID
python invalidate_cloudfront.py /css/villareal-turquoise.css
```

---

## Step 3: Verify It Worked

After 1-5 minutes:

```bash
# Check CloudFront ETag
curl -sI "https://d24pmr7604s8mt.cloudfront.net/css/villareal-turquoise.css" | grep -i ETag

# Check S3 ETag (should match)
curl -sI "https://lcstatic.s3.amazonaws.com/css/villareal-turquoise.css" | grep -i ETag

# If ETags match, CloudFront is serving the new file! ✅
```

Or use the comparison script:
```bash
./check_cloudfront_file.sh \
  "https://d24pmr7604s8mt.cloudfront.net/css/villareal-turquoise.css" \
  "css/villareal-turquoise.css"
```

---

## Why This Happens

### The Flow

```
1. Render Deploy:
   └─> collectstatic runs
       └─> Uploads new file to S3 ✅
           └─> S3 now has latest file

2. Heroku Request:
   └─> User visits www.localchurches.org
       └─> Heroku uses CloudFront
           └─> CloudFront checks cache
               └─> Cache still has old file (17 hours old) ❌
                   └─> Serves old cached file

3. After Invalidation:
   └─> CloudFront cache cleared
       └─> Next request fetches from S3
           └─> Gets new file ✅
               └─> Caches new file
```

### Timeline

- **17 hours ago:** CloudFront cached the file (or last invalidation)
- **Recently:** Render deployed, uploaded new file to S3
- **Now:** 
  - S3 = new file ✅
  - CloudFront cache = old file ❌
  - Heroku serves from CloudFront = old file ❌

---

## Quick Fix Command

Once you have the Distribution ID:

```bash
# Invalidate the specific file
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/css/villareal-turquoise.css"

# Or invalidate all CSS files (counts as 1 path)
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/css/*"
```

---

## Long-Term Solution: Auto-Invalidate

Add to Render's `build.sh` to auto-invalidate after deploy:

```bash
# After collectstatic in build.sh
if [ -n "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
    echo "Invalidating Heroku CloudFront cache..."
    aws cloudfront create-invalidation \
      --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
      --paths "/css/*" "/js/*" || echo "Warning: CloudFront invalidation failed"
fi
```

Then set in Render environment variables:
```
CLOUDFRONT_DISTRIBUTION_ID=E1234567890ABC
```

This way, every Render deploy will automatically invalidate Heroku's CloudFront cache.

---

## Summary

**Problem:** Heroku CloudFront cache is stale (17 hours old)

**Solution:** Invalidate CloudFront cache for `/css/villareal-turquoise.css`

**Steps:**
1. Find Distribution ID (AWS Console or CLI)
2. Create invalidation
3. Wait 1-5 minutes
4. Hard refresh browser

**CloudFront Domain Found:** `d24pmr7604s8mt.cloudfront.net`
