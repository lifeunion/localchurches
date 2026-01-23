# Diagnose S3 Connection Issues

## What I've Added

I've added comprehensive S3 diagnostics that will:

1. **Check if S3 credentials are detected** - Logs whether bucket name, access key, and secret key are set
2. **Test S3 connection** - Attempts to connect to S3 and verify bucket accessibility
3. **Show which storage backend is active** - Clearly indicates if S3 or WhiteNoise is being used
4. **Display expected URLs** - Shows what STATIC_URL should be

---

## How to Check

### Step 1: Check Render Build Logs

After the next deploy, look for these debug messages in the build logs:

**S3 Configuration Check:**
```
DEBUG S3 Config: bucket=True, access_key=True, secret_key=True
DEBUG S3 Bucket Name: lcstatic
DEBUG S3 Access Key: AKIAXXXX...
```

**Storage Backend Selection:**
```
DEBUG: Configuring S3 storage backend
DEBUG: STATIC_URL will be: https://lcstatic.s3.amazonaws.com/
✅ S3 connection successful - bucket 'lcstatic' is accessible
```

**OR if WhiteNoise:**
```
DEBUG: Using WhiteNoise for static files
DEBUG: STATIC_ROOT = /opt/render/project/src/staticfiles
DEBUG: STATIC_URL = /static/
```

---

### Step 2: Check Environment Variable Names

**The code expects these exact variable names:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `S3_BUCKET_NAME` ← **Important: This is `S3_BUCKET_NAME`, not `AWS_STORAGE_BUCKET_NAME`**

**In Render Dashboard:**
1. Go to your service → Environment
2. Verify these exact names are used
3. Check that values are not empty

**Common Issues:**
- Variable name typo (e.g., `AWS_ACCESS_KEY` instead of `AWS_ACCESS_KEY_ID`)
- Variable name mismatch (e.g., `AWS_STORAGE_BUCKET_NAME` instead of `S3_BUCKET_NAME`)
- Empty values (whitespace, quotes, etc.)

---

### Step 3: Check S3 Connection Test Results

**In build logs, look for:**

**✅ Success:**
```
✅ S3 connection successful - bucket 'lcstatic' is accessible
```

**❌ Failure - Common Errors:**

**403 Forbidden:**
```
⚠️  S3 connection issue - Error: 403
```
**Cause:** Credentials don't have permission to access the bucket
**Fix:** Check IAM policy for the AWS user

**404 Not Found:**
```
⚠️  S3 connection issue - Error: 404
```
**Cause:** Bucket name is wrong or bucket doesn't exist
**Fix:** Verify bucket name matches exactly

**InvalidAccessKeyId:**
```
❌ S3 credentials invalid or missing
```
**Cause:** Access key ID is wrong
**Fix:** Verify AWS_ACCESS_KEY_ID is correct

**SignatureDoesNotMatch:**
```
⚠️  S3 connection issue - Error: SignatureDoesNotMatch
```
**Cause:** Secret access key is wrong
**Fix:** Verify AWS_SECRET_ACCESS_KEY is correct

---

### Step 4: Verify STATIC_URL in Runtime

**After deploy, check what STATIC_URL is actually set to:**

**Option A: Check Render Logs (Runtime)**
Look for startup logs that show:
```
DEBUG: STATIC_URL = https://lcstatic.s3.amazonaws.com/
```

**Option B: Check Browser Network Tab**
1. Open admin page
2. F12 → Network tab
3. Look at CSS/JS file URLs
4. Should be: `https://lcstatic.s3.amazonaws.com/wagtailadmin/css/core.css`
5. If it's: `/static/wagtailadmin/css/core.css` → WhiteNoise is being used

---

## Common Issues and Fixes

### Issue 1: Environment Variables Not Detected

**Symptoms:**
- Build logs show: `bucket=False, access_key=False, secret_key=False`
- Using WhiteNoise instead of S3

**Possible Causes:**
1. Variables not set in Render
2. Variable names don't match exactly
3. Variables are in wrong service/environment

**Fix:**
1. Render Dashboard → Your Service → Environment
2. Add/verify these exact names:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `S3_BUCKET_NAME`
3. Redeploy

---

### Issue 2: S3 Connection Fails

**Symptoms:**
- Build logs show: `⚠️  S3 connection issue - Error: XXX`
- Files return 404

**Possible Causes:**
1. Wrong AWS credentials
2. Bucket doesn't exist
3. Credentials don't have permission
4. Wrong AWS region

**Fix:**
1. Verify credentials in AWS Console
2. Test credentials locally: `aws s3 ls s3://lcstatic/`
3. Check IAM policy for bucket access
4. Verify bucket region matches `AWS_S3_REGION_NAME` (default: `us-east-1`)

---

### Issue 3: S3 Configured But Still Using WhiteNoise

**Symptoms:**
- Build logs show S3 is configured
- But browser shows `/static/` URLs (not S3 URLs)

**Possible Causes:**
1. WhiteNoise middleware is still active
2. STATIC_URL is being overridden somewhere
3. Template is using hardcoded `/static/` paths

**Fix:**
1. Check `MIDDLEWARE` - WhiteNoise should be removed if using S3
2. Check for any `STATIC_URL` overrides in settings
3. Verify templates use `{% static %}` tag (not hardcoded paths)

---

## Next Steps

1. **Wait for deploy to complete**
2. **Check build logs** for S3 diagnostics
3. **Check runtime logs** for STATIC_URL
4. **Test in browser** - Check Network tab for file URLs
5. **Report findings** - Share what the logs show

---

## Quick Test Commands

**If you have shell access to Render (or locally with same env vars):**

```bash
# Test S3 connection
python -c "
import os
import boto3
from botocore.exceptions import ClientError

access_key = os.environ.get('AWS_ACCESS_KEY_ID')
secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
bucket = os.environ.get('S3_BUCKET_NAME')

print(f'Access Key: {bool(access_key)}')
print(f'Secret Key: {bool(secret_key)}')
print(f'Bucket: {bucket}')

if access_key and secret_key and bucket:
    try:
        s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        s3.head_bucket(Bucket=bucket)
        print('✅ S3 connection successful')
    except ClientError as e:
        print(f'❌ S3 error: {e.response.get(\"Error\", {}).get(\"Code\")}')
else:
    print('❌ Missing credentials')
"
```
