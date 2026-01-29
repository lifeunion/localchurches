# Why Heroku Shows Old File Version (17 Hours Ago)

## The Problem

- **Render deploy:** Shows latest file version ✅
- **Heroku deploy:** Shows old file version (17 hours ago) ❌

## Root Cause

Both Heroku and Render are using the **same S3 bucket** (`lcstatic`), but:

1. **Render** uploads new files to S3 during `collectstatic`
2. **Heroku** uses **CloudFront** in front of S3
3. **CloudFront cache** hasn't been invalidated, so it's still serving the old file

## What's Happening

```
Render Deploy Flow:
1. Render runs `collectstatic` → Uploads new files to S3 ✅
2. Render serves files directly from S3 (or its own CloudFront) → Sees new files ✅

Heroku Flow:
1. Heroku uses CloudFront → CloudFront caches files
2. CloudFront hasn't been invalidated → Still serving cached old file ❌
3. S3 has new file, but CloudFront cache is stale
```

## The Solution: Invalidate CloudFront Cache

Since Heroku uses CloudFront, you need to invalidate the CloudFront cache after Render uploads new files to S3.

### Step 1: Find Your CloudFront Distribution ID

**Option A: AWS Console**
1. Go to: https://console.aws.amazon.com/cloudfront/
2. Look for distribution serving `www.localchurches.org` or `lcstatic.s3.amazonaws.com`
3. Copy the Distribution ID (starts with `E`)

**Option B: Check Heroku Config**
- Heroku might have CloudFront distribution ID in environment variables
- Check: `heroku config` or Heroku dashboard

**Option C: Check HTML Source**
```bash
# Check what domain Heroku is using for static files
curl -s https://www.localchurches.org | grep -o 'https://[^"]*\.css' | head -5
# If it shows *.cloudfront.net, that's your CloudFront domain
```

### Step 2: Invalidate CloudFront Cache

**Using AWS Console (Easiest):**
1. Go to: https://console.aws.amazon.com/cloudfront/
2. Click your distribution
3. Click "Invalidations" tab
4. Click "Create invalidation"
5. Enter: `/css/villareal-turquoise.css` (or `/css/*` for all CSS)
6. Click "Create invalidation"
7. Wait 1-5 minutes

**Using AWS CLI:**
```bash
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/css/villareal-turquoise.css"
```

**Using Python Script:**
```bash
export CLOUDFRONT_DISTRIBUTION_ID=YOUR_DISTRIBUTION_ID
python invalidate_cloudfront.py /css/villareal-turquoise.css
```

### Step 3: Verify It Worked

After 1-5 minutes:
```bash
# Check if CloudFront ETag matches S3 ETag
curl -sI "https://your-cloudfront-domain.cloudfront.net/css/villareal-turquoise.css" | grep -i ETag
curl -sI "https://lcstatic.s3.amazonaws.com/css/villareal-turquoise.css" | grep -i ETag

# Should match!
```

---

## Why This Happens

### Render vs Heroku Static File Setup

**Render:**
- Runs `collectstatic` on every deploy
- Uploads files to S3 immediately
- May use direct S3 URLs or its own CloudFront (if configured)
- Sees new files right away

**Heroku:**
- Uses CloudFront CDN in front of S3
- CloudFront caches files for performance
- Cache TTL (Time To Live) can be hours/days
- Needs manual invalidation to see new files

### Timeline

1. **17 hours ago:** Last time CloudFront cache was invalidated (or file was first cached)
2. **Recently:** Render deployed and uploaded new file to S3
3. **Now:** 
   - S3 has new file ✅
   - CloudFront still has old cached file ❌
   - Heroku serves from CloudFront → sees old file ❌

---

## Long-Term Solutions

### Option 1: Auto-Invalidate CloudFront After Render Deploy

Add CloudFront invalidation to Render's `build.sh`:

```bash
# After collectstatic in build.sh
if [ -n "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
    echo "Invalidating CloudFront cache..."
    aws cloudfront create-invalidation \
      --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
      --paths "/css/*" "/js/*" || echo "Warning: CloudFront invalidation failed"
fi
```

**Pros:**
- ✅ Automatic invalidation after every deploy
- ✅ Heroku always sees latest files

**Cons:**
- ⚠️ Requires AWS credentials in Render
- ⚠️ Adds ~1-5 minutes to deploy time (waiting for invalidation)

### Option 2: Separate S3 Buckets

**For Heroku:**
- Keep using `lcstatic` bucket
- Keep CloudFront setup

**For Render:**
- Create new bucket: `lcstatic-render`
- Update Render env var: `S3_BUCKET_NAME=lcstatic-render`
- Render uses its own bucket, doesn't affect Heroku

**Pros:**
- ✅ Complete isolation
- ✅ No risk of affecting Heroku production

**Cons:**
- ⚠️ Need to manage two buckets
- ⚠️ More complex setup

### Option 3: Use WhiteNoise for Render

**For Render:**
- Remove S3 credentials from Render
- Render will use WhiteNoise (serves files directly from app)
- No S3 uploads, no CloudFront needed

**For Heroku:**
- Keep using S3 + CloudFront

**Pros:**
- ✅ Render doesn't affect Heroku at all
- ✅ Simpler for Render (no S3 needed)
- ✅ Faster deploys (no S3 upload)

**Cons:**
- ⚠️ Render serves files from app server (less scalable)
- ⚠️ Different static file serving methods

---

## Quick Fix (Right Now)

**To see the new file on Heroku immediately:**

1. **Find CloudFront Distribution ID** (see Step 1 above)
2. **Create invalidation:**
   ```bash
   aws cloudfront create-invalidation \
     --distribution-id YOUR_DISTRIBUTION_ID \
     --paths "/css/villareal-turquoise.css"
   ```
3. **Wait 1-5 minutes**
4. **Hard refresh browser** (Ctrl+Shift+R or Cmd+Shift+R)
5. **Verify:** Check `www.localchurches.org` - should see new file

---

## How to Check Which CloudFront Distribution Heroku Uses

### Method 1: Check HTML Source

```bash
curl -s https://www.localchurches.org | grep -o 'https://[^"]*\.css' | head -5
```

If URLs show `*.cloudfront.net`, that's your CloudFront domain.

### Method 2: Check Browser Network Tab

1. Open `www.localchurches.org` in browser
2. Open Developer Tools (F12)
3. Go to Network tab
4. Reload page
5. Find your CSS file
6. Check "Request URL" - if it's `*.cloudfront.net`, that's CloudFront

### Method 3: AWS Console

1. Go to CloudFront console
2. Look for distribution with:
   - Origin: `lcstatic.s3.amazonaws.com`
   - Or custom domain pointing to Heroku

---

## Summary

**The Issue:**
- Render uploads new files to S3 ✅
- Heroku uses CloudFront (cached) ❌
- CloudFront cache is stale (17 hours old)

**The Fix:**
- Invalidate CloudFront cache for the file path
- Wait 1-5 minutes
- Heroku will see new file

**Long-term:**
- Auto-invalidate after Render deploys, OR
- Use separate S3 buckets, OR
- Use WhiteNoise for Render
