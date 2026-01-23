# How to Revert S3 Static File Changes (Past 4 Days)

## Overview

If S3 bucket versioning is enabled, you can restore previous versions of files. If not, you'll need to restore from backups or re-upload old files.

---

## Method 1: S3 Versioning (If Enabled)

### Step 1: Check if Versioning is Enabled

1. Go to **AWS Console** → **S3** → **lcstatic** bucket
2. Click **Properties** tab
3. Scroll to **Bucket Versioning**
4. Check if it says "Enabled" or "Disabled"

### Step 2: If Versioning is Enabled

**Option A: Restore via AWS Console**

1. Go to **S3 Console** → **lcstatic** bucket
2. Navigate to the file you want to restore (e.g., `wagtailadmin/css/core.css`)
3. Click the file name
4. Click **Versions** tab
5. Find the version from **before 4 days ago**
6. Select the old version
7. Click **Actions** → **Make current version**

**Option B: Restore via AWS CLI**

```bash
# List all versions of a file
aws s3api list-object-versions \
  --bucket lcstatic \
  --prefix wagtailadmin/css/core.css

# Restore a specific version
aws s3api restore-object \
  --bucket lcstatic \
  --key wagtailadmin/css/core.css \
  --version-id <VERSION_ID>
```

**Option C: Restore All Files from 4+ Days Ago**

```bash
# This is complex - you'd need to:
# 1. List all files modified in last 4 days
# 2. For each file, find version from before that date
# 3. Restore that version

# Example script (run at your own risk):
aws s3api list-object-versions --bucket lcstatic --prefix wagtailadmin/ \
  | jq '.Versions[] | select(.LastModified < "2026-01-19")' \
  | while read version; do
      KEY=$(echo $version | jq -r '.Key')
      VERSION_ID=$(echo $version | jq -r '.VersionId')
      aws s3api restore-object --bucket lcstatic --key "$KEY" --version-id "$VERSION_ID"
    done
```

---

## Method 2: Restore from Git/Backup

### Step 1: Identify Changed Files

Check what files were changed in the last 4 days:

```bash
# In your local repository
cd /Users/andreekurniawan/localchurches/localchurches

# Find static files that were modified
git log --since="4 days ago" --name-only --pretty=format: \
  | grep -E "^static/" \
  | sort -u
```

### Step 2: Restore from Git

If you have the old static files in your Git history:

```bash
# Checkout old version of static files
git checkout HEAD@{4.days.ago} -- static/

# Or checkout specific commit before changes
git checkout <COMMIT_HASH> -- static/

# Then re-upload to S3
python manage.py collectstatic --noinput
# (This will upload to S3 if credentials are set)
```

### Step 3: Re-upload to S3

```bash
# Make sure S3 credentials are set
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export S3_BUCKET_NAME="lcstatic"

# Collect and upload static files
python manage.py collectstatic --noinput
```

---

## Method 3: Restore from Heroku Backup

If Heroku has a backup of the static files:

### Option A: Heroku S3 Backup (if configured)

1. Check if Heroku has S3 backups enabled
2. Restore from backup snapshot

### Option B: Download from Heroku Production

If Heroku production is still serving the old files correctly:

```bash
# Download static files from Heroku production
wget -r -np -nH --cut-dirs=1 \
  https://www.localchurches.org/static/ \
  -P ./static_backup/

# Then upload to S3
aws s3 sync ./static_backup/ s3://lcstatic/ --delete
```

---

## Method 4: Manual File Restoration

### Step 1: Identify Files to Restore

Based on your description, these files likely changed:
- `wagtailadmin/css/*.css` (admin CSS files)
- `wagtailadmin/js/*.js` (admin JS files)
- `css/villareal-turquoise.css` (custom CSS)
- `js/villareal/*.js` (custom JS)

### Step 2: Get Old Versions

**From Git:**
```bash
# Get file from 5 days ago
git show HEAD@{5.days.ago}:static/wagtailadmin/css/core.css > core.css.old
```

**From S3 Versioning (if enabled):**
```bash
# Download old version
aws s3api get-object \
  --bucket lcstatic \
  --key wagtailadmin/css/core.css \
  --version-id <OLD_VERSION_ID> \
  core.css.old
```

### Step 3: Upload Old Versions to S3

```bash
# Upload restored file
aws s3 cp core.css.old s3://lcstatic/wagtailadmin/css/core.css
```

---

## Method 5: Enable Versioning and Restore (If Not Already Enabled)

### Step 1: Enable Versioning

```bash
# Enable versioning on bucket
aws s3api put-bucket-versioning \
  --bucket lcstatic \
  --versioning-configuration Status=Enabled
```

**Note**: This won't help with past changes, but will help with future changes.

### Step 2: Use Lifecycle Rules to Manage Versions

```bash
# Set lifecycle rule to keep versions for 30 days
aws s3api put-bucket-lifecycle-configuration \
  --bucket lcstatic \
  --lifecycle-configuration file://lifecycle.json
```

Where `lifecycle.json` contains:
```json
{
  "Rules": [{
    "Id": "KeepVersions30Days",
    "Status": "Enabled",
    "NoncurrentVersionExpiration": {
      "NoncurrentDays": 30
    }
  }]
}
```

---

## Recommended Approach

### For Immediate Fix:

1. **Check S3 Versioning Status**
   - If enabled → Use Method 1 to restore
   - If disabled → Continue to step 2

2. **Check Git History**
   - If static files are in Git → Use Method 2
   - If not → Continue to step 3

3. **Download from Heroku Production**
   - If Heroku still has old files → Use Method 3
   - If not → Continue to step 4

4. **Manual Restoration**
   - Identify specific files that broke
   - Restore only those files (Method 4)

### For Long-term Solution:

1. **Enable S3 Versioning** (Method 5)
   - Protects against future accidental overwrites
   - Allows easy rollback

2. **Separate Render from Heroku**
   - Use WhiteNoise on Render (prevents future conflicts)
   - Keep S3 on Heroku (production stability)

---

## Quick Check Commands

```bash
# Check S3 versioning status
aws s3api get-bucket-versioning --bucket lcstatic

# List recent file modifications (last 4 days)
aws s3 ls s3://lcstatic/wagtailadmin/ --recursive \
  | awk '$1 >= "2026-01-19"'

# Check if specific file has versions
aws s3api list-object-versions \
  --bucket lcstatic \
  --prefix wagtailadmin/css/core.css \
  --max-items 10
```

---

## Important Notes

⚠️ **Before Restoring:**
- Make a backup of current S3 state
- Test restoration on a single file first
- Verify the old version works correctly

⚠️ **After Restoring:**
- Clear CDN cache (if using CloudFront)
- Test production site thoroughly
- Monitor for any issues

⚠️ **Prevention:**
- Enable S3 versioning
- Separate Render and Heroku static files
- Consider using WhiteNoise on Render

---

## Need Help?

If you need assistance:
1. Check S3 versioning status first
2. Share the status (enabled/disabled)
3. I can provide specific commands for your situation
