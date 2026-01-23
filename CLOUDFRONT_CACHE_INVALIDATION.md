# CloudFront Cache Invalidation Guide

## Quick Methods to Invalidate CloudFront Cache

### Method 1: AWS Console (Easiest)

1. **Go to AWS CloudFront Console**
   - Navigate to: https://console.aws.amazon.com/cloudfront/
   - Or: AWS Console → Services → CloudFront

2. **Select Your Distribution**
   - Find the distribution that serves your S3 bucket (`lcstatic`)
   - Click on the distribution ID

3. **Create Invalidation**
   - Click the **"Invalidations"** tab
   - Click **"Create invalidation"** button

4. **Enter Paths**
   - **For a specific file:**
     ```
     /path/to/your/file.css
     /path/to/your/file.js
     ```
   
   - **For all files in a directory:**
     ```
     /static/css/*
     /static/js/*
     ```
   
   - **For everything (use sparingly - costs money!):**
     ```
     /*
     ```

5. **Create Invalidation**
   - Click **"Create invalidation"**
   - Wait 1-5 minutes for propagation

---

### Method 2: AWS CLI (Fastest)

#### Install AWS CLI (if not installed)
```bash
# macOS
brew install awscli

# Or via pip
pip install awscli
```

#### Configure AWS Credentials
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter default region (e.g., us-east-1)
# Enter default output format (json)
```

#### Invalidate Specific File
```bash
# Replace DISTRIBUTION_ID with your CloudFront distribution ID
# Replace /path/to/file.css with your file path

aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/path/to/file.css"
```

#### Invalidate Multiple Files
```bash
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/static/css/file1.css" "/static/js/file2.js" "/static/images/logo.png"
```

#### Invalidate Directory (All Files)
```bash
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/static/css/*" "/static/js/*"
```

#### Invalidate Everything (⚠️ Expensive!)
```bash
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

#### Find Your Distribution ID
```bash
# List all CloudFront distributions
aws cloudfront list-distributions --query "DistributionList.Items[*].[Id,DomainName,Origins.Items[0].DomainName]" --output table
```

---

### Method 3: Python Script (Automated)

Create a script to invalidate cache programmatically:

```python
#!/usr/bin/env python3
"""
CloudFront Cache Invalidation Script
Usage: python invalidate_cloudfront.py /path/to/file.css
"""

import boto3
import sys
import os

# Get distribution ID from environment or hardcode
DISTRIBUTION_ID = os.environ.get('CLOUDFRONT_DISTRIBUTION_ID', 'YOUR_DISTRIBUTION_ID')

def invalidate_cache(paths):
    """Invalidate CloudFront cache for given paths."""
    client = boto3.client('cloudfront')
    
    try:
        response = client.create_invalidation(
            DistributionId=DISTRIBUTION_ID,
            InvalidationBatch={
                'Paths': {
                    'Quantity': len(paths),
                    'Items': paths
                },
                'CallerReference': f'invalidation-{int(time.time())}'
            }
        )
        print(f"✅ Invalidation created: {response['Invalidation']['Id']}")
        print(f"Status: {response['Invalidation']['Status']}")
        return response
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == '__main__':
    import time
    
    if len(sys.argv) < 2:
        print("Usage: python invalidate_cloudfront.py /path/to/file.css")
        print("   or: python invalidate_cloudfront.py /static/css/*")
        sys.exit(1)
    
    paths = sys.argv[1:]
    invalidate_cache(paths)
```

**Usage:**
```bash
# Set distribution ID
export CLOUDFRONT_DISTRIBUTION_ID=YOUR_DISTRIBUTION_ID

# Invalidate specific file
python invalidate_cloudfront.py /static/css/villareal-turquoise.css

# Invalidate multiple files
python invalidate_cloudfront.py /static/css/* /static/js/*
```

---

### Method 4: Django Management Command

Create a Django management command for easy invalidation:

```python
# lampstands/core/management/commands/invalidate_cloudfront.py
from django.core.management.base import BaseCommand
from django.conf import settings
import boto3
import time

class Command(BaseCommand):
    help = 'Invalidate CloudFront cache for static files'

    def add_arguments(self, parser):
        parser.add_argument(
            'paths',
            nargs='+',
            help='Paths to invalidate (e.g., /static/css/file.css)'
        )
        parser.add_argument(
            '--distribution-id',
            type=str,
            help='CloudFront distribution ID (or set CLOUDFRONT_DISTRIBUTION_ID env var)',
        )

    def handle(self, *args, **options):
        distribution_id = options.get('distribution_id') or \
                         getattr(settings, 'CLOUDFRONT_DISTRIBUTION_ID', None) or \
                         os.environ.get('CLOUDFRONT_DISTRIBUTION_ID')
        
        if not distribution_id:
            self.stdout.write(
                self.style.ERROR('CloudFront distribution ID not found. '
                               'Set CLOUDFRONT_DISTRIBUTION_ID env var or use --distribution-id')
            )
            return
        
        paths = options['paths']
        client = boto3.client('cloudfront')
        
        try:
            response = client.create_invalidation(
                DistributionId=distribution_id,
                InvalidationBatch={
                    'Paths': {
                        'Quantity': len(paths),
                        'Items': paths
                    },
                    'CallerReference': f'invalidation-{int(time.time())}'
                }
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Invalidation created: {response["Invalidation"]["Id"]}\n'
                    f'Status: {response["Invalidation"]["Status"]}'
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))
```

**Usage:**
```bash
python manage.py invalidate_cloudfront /static/css/villareal-turquoise.css
python manage.py invalidate_cloudfront /static/css/* --distribution-id YOUR_ID
```

---

## Finding Your CloudFront Distribution ID

### Option 1: AWS Console
1. Go to CloudFront console
2. Look for distribution with origin pointing to `lcstatic.s3.amazonaws.com`
3. Copy the Distribution ID (starts with `E`)

### Option 2: AWS CLI
```bash
aws cloudfront list-distributions \
  --query "DistributionList.Items[?Origins.Items[0].DomainName=='lcstatic.s3.amazonaws.com'].[Id,DomainName]" \
  --output table
```

### Option 3: Check Your Domain
If you're using a CloudFront domain, check the HTML source of your site:
```bash
curl -s https://www.localchurches.org | grep -o 'https://[^"]*\.cloudfront\.net[^"]*'
```

---

## Best Practices

### ✅ DO:
- **Invalidate specific files** when possible (cheaper)
- **Use versioned filenames** (e.g., `file.v123.css`) to avoid invalidation
- **Invalidate directories** for related files (`/static/css/*`)
- **Wait 1-5 minutes** after invalidation before testing

### ❌ DON'T:
- **Don't invalidate `/*`** unless absolutely necessary (first 1,000 paths/month are free, then $0.005 per path)
- **Don't invalidate too frequently** (cache is there for performance)
- **Don't forget** that invalidation takes time to propagate globally

---

## Cost Considerations

- **First 1,000 paths/month**: FREE
- **After 1,000 paths/month**: $0.005 per path

**Examples:**
- Invalidating `/static/css/file.css` = 1 path
- Invalidating `/static/css/*` = 1 path (wildcard counts as 1)
- Invalidating `/*` = 1 path (but invalidates everything)

**Tip:** Use wildcards (`/*`) for directories instead of listing individual files.

---

## Troubleshooting

### Cache Still Not Updated?

1. **Wait longer** (can take 5-15 minutes globally)
2. **Check invalidation status** in CloudFront console
3. **Hard refresh browser** (Ctrl+Shift+R or Cmd+Shift+R)
4. **Clear browser cache** completely
5. **Test in incognito mode**
6. **Check if file was actually uploaded** to S3
7. **Verify CloudFront distribution** is pointing to correct S3 bucket

### Verify File in S3
```bash
aws s3 ls s3://lcstatic/path/to/file.css
```

### Check CloudFront Cache Headers
```bash
curl -I https://your-cloudfront-domain.cloudfront.net/path/to/file.css
# Look for Cache-Control, ETag headers
```

---

## Quick Reference

```bash
# 1. Find distribution ID
aws cloudfront list-distributions --output table

# 2. Invalidate specific file
aws cloudfront create-invalidation \
  --distribution-id E1234567890ABC \
  --paths "/static/css/villareal-turquoise.css"

# 3. Check invalidation status
aws cloudfront get-invalidation \
  --distribution-id E1234567890ABC \
  --id I1234567890ABC
```

---

## Alternative: Use Versioned Filenames

Instead of invalidating cache, use versioned filenames:

```python
# In Django settings
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
```

This automatically appends hash to filenames:
- `file.css` → `file.a1b2c3d4.css`
- Browser requests new file when hash changes
- No cache invalidation needed!

---

## Summary

**Fastest method:** AWS CLI
```bash
aws cloudfront create-invalidation --distribution-id YOUR_ID --paths "/path/to/file.css"
```

**Easiest method:** AWS Console → CloudFront → Invalidations → Create invalidation

**Best practice:** Use versioned filenames to avoid invalidation entirely.
