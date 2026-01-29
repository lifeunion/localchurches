# Quick AWS CLI Setup - Next Steps

## ✅ AWS CLI is Installed!

AWS CLI has been successfully installed. Now you need to configure it with your AWS credentials.

---

## Step 1: Get Your AWS Credentials

You need your **AWS Access Key ID** and **Secret Access Key**.

### To Get Your Credentials:

1. **Go to AWS Console:** https://console.aws.amazon.com/
2. **Click your username** (top right corner)
3. **Click "Security credentials"**
4. **Scroll down to "Access keys"** section
5. **Click "Create access key"**
6. **Select use case:** "Command Line Interface (CLI)"
7. **Click "Next"** → **"Create access key"**
8. **IMPORTANT:** Copy both:
   - **Access Key ID** (starts with `AKIA...`)
   - **Secret Access Key** (shown only once - save it!)

---

## Step 2: Configure AWS CLI

Run this command and enter your credentials when prompted:

```bash
aws configure
```

**You'll be asked for:**

1. **AWS Access Key ID:** `[Paste your Access Key ID]`
2. **AWS Secret Access Key:** `[Paste your Secret Access Key]`
3. **Default region name:** `us-east-1` (or your preferred region)
4. **Default output format:** `json` (just press Enter)

**Example:**
```
AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
Default region name [None]: us-east-1
Default output format [None]: json
```

---

## Step 3: Test Your Setup

```bash
# Test connection - list your S3 buckets
aws s3 ls

# Should show your buckets, including 'lcstatic'
```

If you see your buckets, you're all set! ✅

---

## Step 4: Find Your CloudFront Distribution ID

```bash
# List all CloudFront distributions
aws cloudfront list-distributions --output table

# Or filter for your S3 bucket
aws cloudfront list-distributions \
  --query "DistributionList.Items[?Origins.Items[0].DomainName=='lcstatic.s3.amazonaws.com'].[Id,DomainName,Status]" \
  --output table
```

**Look for the Distribution ID** (starts with `E`, e.g., `E1234567890ABC`)

---

## Step 5: Invalidate CloudFront Cache

Once you have your Distribution ID:

```bash
# Replace YOUR_DISTRIBUTION_ID with your actual ID
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/css/villareal-turquoise.css"
```

**Or use the quick script:**
```bash
./quick_invalidate.sh YOUR_DISTRIBUTION_ID
```

---

## Troubleshooting

### "Unable to locate credentials"

Make sure you ran `aws configure` and entered your credentials correctly.

### "Access Denied"

Check that your AWS user has permissions for:
- S3 (read access)
- CloudFront (invalidation permissions)

### Can't find Distribution ID

Make sure you're looking at the right AWS account/region. Your CloudFront distribution should have an origin pointing to `lcstatic.s3.amazonaws.com`.

---

## Quick Commands Reference

```bash
# List S3 buckets
aws s3 ls

# List files in bucket
aws s3 ls s3://lcstatic/css/

# Check file metadata
aws s3api head-object --bucket lcstatic --key css/villareal-turquoise.css

# List CloudFront distributions
aws cloudfront list-distributions --output table

# Create invalidation
aws cloudfront create-invalidation \
  --distribution-id YOUR_ID \
  --paths "/css/villareal-turquoise.css"
```

---

## Next: Configure Your Credentials

Run this now:
```bash
aws configure
```

Then follow the prompts to enter your AWS Access Key ID and Secret Access Key.
