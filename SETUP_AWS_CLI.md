# Setting Up AWS CLI

## Quick Setup Guide

### Step 1: Install AWS CLI

#### Option A: Using Homebrew (Recommended for macOS)

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install AWS CLI
brew install awscli
```

#### Option B: Using pip (Python package manager)

```bash
# Install AWS CLI via pip
pip3 install awscli

# Or if you prefer user installation (no sudo needed)
pip3 install --user awscli
```

#### Option C: Using Installer (macOS)

```bash
# Download and install AWS CLI v2
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
```

---

### Step 2: Verify Installation

```bash
# Check if AWS CLI is installed
aws --version

# Should show something like:
# aws-cli/2.x.x Python/3.x.x Darwin/xx.x.x source/x86_64
```

---

### Step 3: Configure AWS Credentials

You need your AWS Access Key ID and Secret Access Key.

**To get your AWS credentials:**

1. **Go to AWS Console:** https://console.aws.amazon.com/
2. **Click your username** (top right) → **Security credentials**
3. **Scroll to "Access keys"** section
4. **Click "Create access key"**
5. **Choose use case** (e.g., "Command Line Interface (CLI)")
6. **Download or copy:**
   - Access Key ID
   - Secret Access Key (only shown once!)

**Configure AWS CLI:**

```bash
aws configure
```

You'll be prompted for:
1. **AWS Access Key ID:** `[Your Access Key ID]`
2. **AWS Secret Access Key:** `[Your Secret Access Key]`
3. **Default region name:** `us-east-1` (or your preferred region)
4. **Default output format:** `json` (recommended)

**Example:**
```
AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
Default region name [None]: us-east-1
Default output format [None]: json
```

---

### Step 4: Test AWS CLI

```bash
# Test connection - list your S3 buckets
aws s3 ls

# Should show your buckets, including 'lcstatic'
```

---

### Step 5: Find Your CloudFront Distribution ID

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

### Step 6: Test CloudFront Invalidation

```bash
# Replace YOUR_DISTRIBUTION_ID with your actual ID
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/css/villareal-turquoise.css"
```

---

## Troubleshooting

### AWS CLI Not Found After Installation

**If using pip:**
```bash
# Add to your PATH (add to ~/.zshrc or ~/.bash_profile)
export PATH="$HOME/Library/Python/3.x/bin:$PATH"

# Then reload shell
source ~/.zshrc  # or source ~/.bash_profile
```

**If using Homebrew:**
```bash
# Should work automatically, but if not:
brew link awscli
```

### Permission Denied

```bash
# Make sure AWS CLI is executable
chmod +x $(which aws)

# Or reinstall with proper permissions
pip3 install --user awscli
```

### Credentials Not Working

1. **Verify credentials are correct:**
   ```bash
   aws sts get-caller-identity
   ```
   Should show your AWS account info.

2. **Check credentials file:**
   ```bash
   cat ~/.aws/credentials
   ```

3. **Reconfigure if needed:**
   ```bash
   aws configure
   ```

### Region Issues

```bash
# Set default region
aws configure set region us-east-1

# Or use --region flag in commands
aws s3 ls --region us-east-1
```

---

## Quick Reference Commands

### S3 Commands

```bash
# List buckets
aws s3 ls

# List files in bucket
aws s3 ls s3://lcstatic/

# List files in directory
aws s3 ls s3://lcstatic/css/

# Check file metadata
aws s3api head-object --bucket lcstatic --key css/villareal-turquoise.css

# Copy file from S3
aws s3 cp s3://lcstatic/css/villareal-turquoise.css /tmp/file.css
```

### CloudFront Commands

```bash
# List distributions
aws cloudfront list-distributions --output table

# Create invalidation
aws cloudfront create-invalidation \
  --distribution-id YOUR_ID \
  --paths "/css/villareal-turquoise.css"

# Check invalidation status
aws cloudfront get-invalidation \
  --distribution-id YOUR_ID \
  --id INVALIDATION_ID

# List recent invalidations
aws cloudfront list-invalidations \
  --distribution-id YOUR_ID \
  --max-items 5
```

---

## Security Best Practices

1. **Don't commit credentials:**
   - Never commit `~/.aws/credentials` to Git
   - Use environment variables or AWS IAM roles when possible

2. **Use IAM users with minimal permissions:**
   - Create a separate IAM user for CLI access
   - Grant only necessary permissions (S3 read, CloudFront invalidation)

3. **Rotate access keys regularly:**
   - Change keys every 90 days
   - Delete old/unused keys

4. **Use profiles for multiple accounts:**
   ```bash
   aws configure --profile production
   aws configure --profile staging
   
   # Use profile
   aws s3 ls --profile production
   ```

---

## Next Steps

Once AWS CLI is set up:

1. **Find your CloudFront Distribution ID:**
   ```bash
   aws cloudfront list-distributions --output table
   ```

2. **Invalidate the cached file:**
   ```bash
   ./quick_invalidate.sh YOUR_DISTRIBUTION_ID
   ```

3. **Or use the Python script:**
   ```bash
   export CLOUDFRONT_DISTRIBUTION_ID=YOUR_DISTRIBUTION_ID
   python invalidate_cloudfront.py /css/villareal-turquoise.css
   ```

---

## Need Help?

- **AWS CLI Documentation:** https://docs.aws.amazon.com/cli/
- **AWS CLI Command Reference:** https://awscli.amazonaws.com/v2/documentation/api/latest/reference/index.html
- **CloudFront Invalidation:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Invalidation.html
