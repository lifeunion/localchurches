# Force CloudFront to Fetch Current S3 File

## Problem
CloudFront is serving a cached file from 17 hours ago, even though S3 has the updated version.

## Solution: Create CloudFront Invalidation

### Method 1: AWS Console (Easiest)

1. **Go to CloudFront Console:**
   - https://console.aws.amazon.com/cloudfront/
   - Or: AWS Console → Services → CloudFront

2. **Find Your Distribution:**
   - Look for the distribution serving `lcstatic` S3 bucket
   - Click on the Distribution ID

3. **Create Invalidation:**
   - Click the **"Invalidations"** tab
   - Click **"Create invalidation"** button

4. **Enter Path:**
   ```
   /css/villareal-turquoise.css
   ```
   (Or use `/css/*` to invalidate all CSS files)

5. **Click "Create invalidation"**
6. **Wait 1-5 minutes** for propagation

---

### Method 2: AWS CLI (Fastest)

```bash
# Replace YOUR_DISTRIBUTION_ID with your actual CloudFront distribution ID
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/css/villareal-turquoise.css"
```

**To find your Distribution ID:**
```bash
aws cloudfront list-distributions \
  --query "DistributionList.Items[?Origins.Items[0].DomainName=='lcstatic.s3.amazonaws.com'].[Id,DomainName]" \
  --output table
```

---

### Method 3: Python Script

```bash
# Set your CloudFront distribution ID
export CLOUDFRONT_DISTRIBUTION_ID=YOUR_DISTRIBUTION_ID

# Run the script
python invalidate_cloudfront.py /css/villareal-turquoise.css
```

---

### Method 4: Invalidate Entire Directory (If Multiple Files Changed)

```bash
# Invalidate all CSS files
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/css/*"
```

**Note:** Wildcards count as 1 path, so this is cost-effective if multiple files changed.

---

## Verify the Invalidation Worked

### Check Invalidation Status

**AWS Console:**
- CloudFront → Your Distribution → Invalidations tab
- Status should show "Completed" (not "In Progress")

**AWS CLI:**
```bash
# List recent invalidations
aws cloudfront list-invalidations \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --max-items 5
```

### Verify File is Updated

**Compare ETags:**
```bash
# CloudFront ETag
CF_ETAG=$(curl -sI "https://your-cf-domain.cloudfront.net/css/villareal-turquoise.css" | grep -i ETag | cut -d' ' -f2 | tr -d '\r"')

# S3 ETag (should be: 5494cb4b85c5a0f7dfeef13da269a74f based on your earlier info)
S3_ETAG="5494cb4b85c5a0f7dfeef13da269a74f"

if [ "$CF_ETAG" = "$S3_ETAG" ]; then
    echo "✅ CloudFront is now serving the current file!"
else
    echo "❌ Still serving old file. Wait a few more minutes or check invalidation status."
fi
```

**Or use the comparison script:**
```bash
./check_cloudfront_file.sh \
  "https://your-cloudfront-domain.cloudfront.net/css/villareal-turquoise.css" \
  "css/villareal-turquoise.css"
```

---

## Timeline

- **Invalidation creation:** Instant
- **Propagation time:** 1-5 minutes (usually)
- **Global propagation:** Up to 15 minutes (rare)

**If still seeing old file after 15 minutes:**
1. Check invalidation status (should be "Completed")
2. Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
3. Test in incognito mode
4. Verify S3 file was actually updated (check Last-Modified date)

---

## Troubleshooting

### Invalidation Still "In Progress"
- Wait a few more minutes
- Large invalidations can take longer
- Check CloudFront service status

### File Still Old After Invalidation
1. **Verify S3 file is updated:**
   ```bash
   aws s3 ls s3://lcstatic/css/villareal-turquoise.css
   # Check Last Modified date
   ```

2. **Check if using correct CloudFront distribution:**
   - You might have multiple distributions
   - Verify which one your site is using

3. **Browser cache:**
   - Hard refresh (Ctrl+Shift+R)
   - Clear browser cache completely
   - Test in incognito mode

4. **Check file path:**
   - Verify the path matches exactly
   - Case-sensitive
   - No trailing slash

---

## Quick Reference

**Invalidate single file:**
```bash
aws cloudfront create-invalidation \
  --distribution-id YOUR_ID \
  --paths "/css/villareal-turquoise.css"
```

**Invalidate directory:**
```bash
aws cloudfront create-invalidation \
  --distribution-id YOUR_ID \
  --paths "/css/*"
```

**Check status:**
```bash
aws cloudfront list-invalidations --distribution-id YOUR_ID --max-items 1
```

---

## Cost Note

- **First 1,000 paths/month:** FREE
- **After 1,000:** $0.005 per path
- **Wildcards (`/*`):** Count as 1 path (even if invalidating thousands of files)

So invalidating `/css/*` is very cost-effective if multiple files changed!
