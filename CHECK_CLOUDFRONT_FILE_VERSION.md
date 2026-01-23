# How to Check File Version Served by CloudFront

## Quick Methods

### Method 1: Check ETag Header (Easiest)

The **ETag** header is a hash of the file content. Compare CloudFront's ETag with S3's ETag:

```bash
# Get CloudFront ETag
curl -sI "https://your-cloudfront-domain.cloudfront.net/css/villareal-turquoise.css" | grep -i ETag

# Get S3 ETag (direct)
curl -sI "https://lcstatic.s3.us-east-1.amazonaws.com/css/villareal-turquoise.css" | grep -i ETag
```

**If ETags match:** CloudFront is serving the same file as S3  
**If ETags differ:** CloudFront is serving a cached/old version

---

### Method 2: Check Last-Modified Header

```bash
# CloudFront
curl -sI "https://your-cloudfront-domain.cloudfront.net/css/villareal-turquoise.css" | grep -i "Last-Modified"

# S3 Direct
curl -sI "https://lcstatic.s3.us-east-1.amazonaws.com/css/villareal-turquoise.css" | grep -i "Last-Modified"
```

**Compare the dates** - CloudFront should match or be close to S3's date.

---

### Method 3: Check File Size

```bash
# CloudFront
curl -sI "https://your-cloudfront-domain.cloudfront.net/css/villareal-turquoise.css" | grep -i "Content-Length"

# S3 Direct
curl -sI "https://lcstatic.s3.us-east-1.amazonaws.com/css/villareal-turquoise.css" | grep -i "Content-Length"
```

**If sizes match:** Likely the same file  
**If sizes differ:** Different versions

---

### Method 4: Compare File Content (Most Reliable)

```bash
# Download and compare
curl -s "https://your-cloudfront-domain.cloudfront.net/css/villareal-turquoise.css" > /tmp/cf_file.css
curl -s "https://lcstatic.s3.us-east-1.amazonaws.com/css/villareal-turquoise.css" > /tmp/s3_file.css

# Compare
diff /tmp/cf_file.css /tmp/s3_file.css

# Or check MD5
md5 /tmp/cf_file.css
md5 /tmp/s3_file.css
```

**If identical:** CloudFront is serving current file  
**If different:** CloudFront cache needs invalidation

---

### Method 5: Check Cache Status

```bash
# Check if CloudFront is serving from cache
curl -sI "https://your-cloudfront-domain.cloudfront.net/css/villareal-turquoise.css" | grep -i "X-Cache"

# Output examples:
# X-Cache: Hit from cloudfront  (serving cached version)
# X-Cache: Miss from cloudfront (fetching from S3)
```

**X-Cache: Hit** = Serving from cache (may be old)  
**X-Cache: Miss** = Fetched from S3 (should be current)

---

### Method 6: Use the Provided Script

I've created a script that does all the checks automatically:

```bash
./check_cloudfront_file.sh \
  "https://your-cloudfront-domain.cloudfront.net/css/villareal-turquoise.css" \
  "css/villareal-turquoise.css"
```

This script will:
- ✅ Compare ETags
- ✅ Compare file sizes
- ✅ Compare Last-Modified dates
- ✅ Show cache status
- ✅ Show file content preview

---

## Using Browser Developer Tools

1. **Open Developer Tools** (F12)
2. **Go to Network tab**
3. **Reload page** (Ctrl+R or Cmd+R)
4. **Find your CSS file** in the network list
5. **Click on it** to see headers:
   - **Response Headers** → Look for `ETag`, `Last-Modified`, `X-Cache`
   - **Request URL** → This shows if it's CloudFront or S3

---

## Using AWS CLI

```bash
# Get S3 object metadata
aws s3api head-object \
  --bucket lcstatic \
  --key css/villareal-turquoise.css

# This shows:
# - ETag (file hash)
# - LastModified (when file was uploaded)
# - ContentLength (file size)
```

Then compare with CloudFront headers.

---

## Quick One-Liner to Check ETag Match

```bash
# Compare ETags
CF_ETAG=$(curl -sI "https://your-cf-domain.cloudfront.net/css/villareal-turquoise.css" | grep -i ETag | cut -d' ' -f2 | tr -d '\r"')
S3_ETAG=$(curl -sI "https://lcstatic.s3.us-east-1.amazonaws.com/css/villareal-turquoise.css" | grep -i ETag | cut -d' ' -f2 | tr -d '\r"')

if [ "$CF_ETAG" = "$S3_ETAG" ]; then
    echo "✅ Files match (ETag: $CF_ETAG)"
else
    echo "❌ Files differ!"
    echo "   CloudFront: $CF_ETAG"
    echo "   S3:         $S3_ETAG"
fi
```

---

## Understanding the Results

### ✅ ETag Match
- **Meaning:** CloudFront is serving the same file as S3
- **Action:** No invalidation needed
- **Note:** Even if ETag matches, CloudFront might still be caching (check `X-Cache: Hit`)

### ❌ ETag Mismatch
- **Meaning:** CloudFront is serving a different/cached version
- **Action:** Create CloudFront invalidation
- **Common causes:**
  - Cache not invalidated after S3 upload
  - CloudFront TTL hasn't expired yet
  - Wrong CloudFront distribution

### X-Cache: Hit
- **Meaning:** Serving from CloudFront cache
- **Action:** If ETag doesn't match S3, invalidate cache

### X-Cache: Miss
- **Meaning:** Fetched fresh from S3
- **Action:** Should match S3 ETag. If not, check CloudFront origin settings

---

## Finding Your CloudFront URL

If you don't know your CloudFront distribution URL:

1. **Check HTML source:**
   ```bash
   curl -s https://www.localchurches.org | grep -o 'https://[^"]*\.css' | head -5
   ```

2. **Check Django settings:**
   - Look for `AWS_S3_CUSTOM_DOMAIN` in `production.py`
   - If it's a CloudFront domain, it will be `*.cloudfront.net`

3. **AWS Console:**
   - CloudFront → Your Distribution → Domain Name

---

## Example Output

```bash
$ ./check_cloudfront_file.sh \
    "https://d1234567890.cloudfront.net/css/villareal-turquoise.css" \
    "css/villareal-turquoise.css"

==========================================
CloudFront vs S3 File Comparison
==========================================

📡 CloudFront Response:
   URL: https://d1234567890.cloudfront.net/css/villareal-turquoise.css
   HTTP/2 200
   ETag: "5494cb4b85c5a0f7dfeef13da269a74f"
   Last-Modified: Thu, 23 Jan 2026 21:30:00 GMT
   Content-Length: 12345
   X-Cache: Hit from cloudfront
   Age: 3600

📦 S3 Direct Response:
   URL: https://lcstatic.s3.us-east-1.amazonaws.com/css/villareal-turquoise.css
   HTTP/1.1 200 OK
   ETag: "5494cb4b85c5a0f7dfeef13da269a74f"
   Last-Modified: Thu, 23 Jan 2026 21:30:00 GMT
   Content-Length: 12345

==========================================
Comparison:
==========================================
✅ ETag Match: Files are identical
   CloudFront: 5494cb4b85c5a0f7dfeef13da269a74f
   S3:         5494cb4b85c5a0f7dfeef13da269a74f

✅ Size Match: 12345 bytes

📦 CloudFront Cache: HIT (serving from cache)
   Age: 3600 seconds
```

---

## Summary

**Fastest method:** Compare ETags
```bash
curl -sI "CF_URL" | grep ETag
curl -sI "S3_URL" | grep ETag
```

**Most reliable:** Use the provided script
```bash
./check_cloudfront_file.sh "CF_URL" "S3_PATH"
```

**If ETags don't match:** Create CloudFront invalidation
