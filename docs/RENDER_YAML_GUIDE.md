# Using render.yaml for Infrastructure as Code

This guide explains how to use the `render.yaml` file to deploy your application to Render.

## What is render.yaml?

`render.yaml` is a Render Blueprint that defines your infrastructure as code. Instead of manually creating services in the Render dashboard, you can define everything in a YAML file and deploy it with one click.

## Benefits

- ✅ **Version controlled** - Your infrastructure is in git
- ✅ **Reproducible** - Easy to recreate or modify
- ✅ **Consistent** - Same configuration every time
- ✅ **Documentation** - Infrastructure is self-documenting

## How to Use

### Step 1: Review render.yaml

Open `render.yaml` and review the configuration:
- Database settings (name, region, plan)
- Web service settings (build command, start command)
- Environment variables (some are pre-configured)

### Step 2: Customize (if needed)

Before deploying, you may want to customize:

1. **Region**: Change `region: oregon` to your preferred region
2. **Plan**: Update `plan: starter` to match your needs
   - `starter` - Free tier (good for testing)
   - `standard` - Production tier
   - `pro` - High performance
3. **ALLOWED_HOSTS**: Update with your actual domain(s)
4. **WAGTAILADMIN_BASE_URL**: Update with your actual domain

### Step 3: Deploy via Blueprint

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **Blueprint**
3. Connect your GitHub repository
4. Render will detect `render.yaml`
5. Review the services that will be created
6. Click **Apply**

### Step 4: Set Secret Environment Variables

After the blueprint creates your services, you need to set secret variables manually:

1. Go to your **Web Service** → **Environment**
2. Set these variables (they're marked as `sync: false` in render.yaml):
   - `SECRET_KEY` - Your Django secret key
   - `AWS_ACCESS_KEY_ID` - AWS S3 access key
   - `AWS_SECRET_ACCESS_KEY` - AWS S3 secret key
   - `SENDGRID_USERNAME` - SendGrid username
   - `SENDGRID_PASSWORD` - SendGrid password
   - `GOOGLE_RECAPTCHA_SITE_KEY` - reCAPTCHA site key
   - `GOOGLE_RECAPTCHA_SECRET_KEY` - reCAPTCHA secret key

3. Update these if needed:
   - `ALLOWED_HOSTS` - Your domain(s), comma-separated
   - `WAGTAILADMIN_BASE_URL` - Your full domain URL

### Step 5: Verify Database Link

The database should be automatically linked (via `fromDatabase` in render.yaml), but verify:

1. Go to **Web Service** → **Environment**
2. Check that `DATABASE_URL` is set
3. If not set, manually link the database:
   - Scroll to **Add Environment Variable**
   - Click **Link Resource** → Select your database

## Environment Variables Reference

### Auto-Configured (via render.yaml)

These are set automatically:
- `DJANGO_SETTINGS_MODULE` = `lampstands.settings.production`
- `DATABASE_URL` = Auto-set from linked database
- `DEBUG` = `False` (secure default)
- `LOG_LEVEL` = `INFO` (production-appropriate)
- Various logging levels (INFO/WARNING defaults)

### Must Set Manually (Secrets)

These must be set in Render dashboard:
- `SECRET_KEY` ⚠️ **REQUIRED**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `SENDGRID_USERNAME`
- `SENDGRID_PASSWORD`
- `GOOGLE_RECAPTCHA_SITE_KEY`
- `GOOGLE_RECAPTCHA_SECRET_KEY`

### Should Update (Domain-specific)

Update these with your actual values:
- `ALLOWED_HOSTS` - Your domain(s)
- `WAGTAILADMIN_BASE_URL` - Your full domain URL
- `S3_BUCKET_NAME` - If different from `lcstatic`

## Updating render.yaml

After making changes to `render.yaml`:

1. Commit and push to your repository
2. In Render dashboard, go to your **Blueprint**
3. Click **Update** or **Redeploy**
4. Render will detect changes and update services

**Note:** Some changes (like plan upgrades) may require manual confirmation in the dashboard.

## Troubleshooting

### Blueprint not detected

- Ensure `render.yaml` is in the root of your repository
- Check that it's committed to git
- Verify YAML syntax is correct

### Database not linked

- Check that database name in `render.yaml` matches the created database
- Manually link if needed (see Step 5 above)

### Environment variables not set

- Variables marked `sync: false` must be set manually
- Check Render dashboard → Environment tab

### Build fails

- Verify `build.sh` has execute permissions
- Check build logs for specific errors
- Ensure all dependencies are in `requirements.txt`

## Running management commands on Render

To run Django management commands against your Render database (e.g. to inspect church data):

1. **Render Shell** (easiest): In the Render dashboard, open your **Web Service** → **Shell** tab. In the shell run:
   ```bash
   python manage.py check_church_contacts Anaheim
   ```
   This prints regular vs consented brother contact data for the Church in Anaheim (or use another locality name).

2. **One-off job**: You can add a Background Worker or one-off job in `render.yaml` that runs a command; for ad-hoc checks, Shell is usually enough.

Example: `python manage.py check_church_contacts Fullerton` or `python manage.py check_church_contacts "Some City" --all` to show all matching churches.

## Alternative: Manual Setup

If you prefer not to use `render.yaml`, you can create services manually in the Render dashboard. See `RENDER_MIGRATION_CHECKLIST.md` for manual setup instructions.

## Next Steps

After deploying with `render.yaml`:

1. ✅ Set all secret environment variables
2. ✅ Migrate your database (see `MANUAL_MIGRATION.md`)
3. ✅ Test your application
4. ✅ Update DNS if using custom domain
5. ✅ Review security settings (DEBUG, ALLOWED_HOSTS)

---

For more information, see:
- [Render Blueprint Documentation](https://render.com/docs/blueprint-spec)
- [Render Environment Variables](https://render.com/docs/environment-variables)
- Your `RENDER_MIGRATION_CHECKLIST.md` for full migration steps
