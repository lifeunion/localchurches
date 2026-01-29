# Heroku → Render Migration Checklist

This guide will help you migrate your production environment from Heroku to Render.

## Pre-Migration: Gather Information

### 1. Export Heroku Environment Variables

Run these commands to get all your Heroku config vars:

```bash
# Replace YOUR_APP_NAME with your Heroku app name
heroku config -a YOUR_APP_NAME > heroku_config.txt
```

**Key variables to document:**
- `SECRET_KEY` - Django secret key
- `DATABASE_URL` - Heroku Postgres connection string
- `AWS_ACCESS_KEY_ID` - AWS S3 access key
- `AWS_SECRET_ACCESS_KEY` - AWS S3 secret key
- `S3_BUCKET_NAME` - S3 bucket name (if different from default)
- `SENDGRID_USERNAME` - SendGrid username
- `SENDGRID_PASSWORD` - SendGrid password
- `GOOGLE_RECAPTCHA_SITE_KEY` - reCAPTCHA site key
- `GOOGLE_RECAPTCHA_SECRET_KEY` - reCAPTCHA secret key
- `WAGTAILADMIN_BASE_URL` - Base URL for Wagtail admin (e.g., https://yourdomain.com)
- Any other custom environment variables

### 2. Verify Current Setup

✅ **Already configured:**
- `Procfile` - Already set up with gunicorn
- `build.sh` - Already configured for Render (runs migrations + collectstatic)
- `production.py` - Already uses `DATABASE_URL` (compatible with Render)
- `requirements.txt` - All dependencies listed
- WhiteNoise configured for static files

## Step 1: Create Render Services

You have two options:

### Option A: Using render.yaml (Infrastructure as Code - Recommended)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **Blueprint**
3. Connect your GitHub repository
4. Render will detect `render.yaml` in your repo
5. Review the configuration and click **Apply**
6. This creates both the database and web service automatically
7. **Then proceed to Step 2** to set environment variables

**Benefits:**
- Infrastructure defined as code
- Easy to recreate or modify
- Version controlled
- Consistent deployments

### Option B: Manual Setup (Alternative)

#### 1.1 Create PostgreSQL Database

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **PostgreSQL**
3. Configure:
   - **Name**: `localchurches-db` (or your preferred name)
   - **Database**: `localchurches` (or your preferred name)
   - **User**: Auto-generated
   - **Region**: Choose closest to your users
   - **PostgreSQL Version**: 15 or 16 (recommended)
   - **Plan**: Choose based on your needs (Free tier available for testing)
4. Click **Create Database**
5. **Important**: Note the **Internal Database URL** and **External Database URL**

#### 1.2 Create Web Service

1. In Render Dashboard, click **New +** → **Web Service**
2. Connect your GitHub repository
3. Configure the service:
   - **Name**: `localchurches` (or your preferred name)
   - **Environment**: `Python 3`
   - **Region**: Same as database
   - **Branch**: `master` (or your production branch)
   - **Root Directory**: Leave empty (or specify if needed)
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn lampstands.wsgi --log-file -`
   - **Plan**: Choose based on your needs

## Step 2: Configure Environment Variables

In your Render Web Service dashboard, go to **Environment** and add:

### Required Variables

```
SECRET_KEY=<your-heroku-secret-key>
DATABASE_URL=<will-be-auto-set-when-you-link-db>
```

### AWS S3 (for media files)

```
AWS_ACCESS_KEY_ID=<your-heroku-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-heroku-aws-secret-key>
S3_BUCKET_NAME=lcstatic
```

### Email (SendGrid)

```
SENDGRID_USERNAME=<your-heroku-sendgrid-username>
SENDGRID_PASSWORD=<your-heroku-sendgrid-password>
```

### reCAPTCHA

```
GOOGLE_RECAPTCHA_SITE_KEY=<your-heroku-recaptcha-site-key>
GOOGLE_RECAPTCHA_SECRET_KEY=<your-heroku-recaptcha-secret-key>
```

### Wagtail

```
WAGTAILADMIN_BASE_URL=https://your-render-app.onrender.com
```

### Security Settings (New - Recommended)

```
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,localchurches.onrender.com
```

**Note:** 
- `DATABASE_URL` will be automatically set when you link the database (see Step 3) or if using `render.yaml`
- If using `render.yaml`, some variables are pre-configured but you still need to set secrets manually

## Step 3: Link Database to Web Service

1. In your Render Web Service dashboard
2. Go to **Environment** tab
3. Scroll down to **Add Environment Variable**
4. Click **Link Resource** → Select your PostgreSQL database
5. This automatically sets `DATABASE_URL`

## Step 4: Migrate Database

You have two options:

### Option A: Manual Migration (Recommended)

Follow the instructions in `MANUAL_MIGRATION.md` - this is the most reliable method since Render's build servers often cannot reach Heroku Postgres.

**Quick summary:**
1. Install PostgreSQL client tools on your machine
2. Get Heroku `DATABASE_URL` from Heroku dashboard
3. Get Render External Database URL from Render dashboard
4. Dump from Heroku: `pg_dump "$HEROKU_DATABASE_URL" --no-owner --no-acl -f ./heroku_dump.sql`
5. Restore to Render: `psql "$RENDER_DATABASE_URL" -f ./heroku_dump.sql`

### Option B: Automatic Migration (if Option A fails)

1. Temporarily add `HEROKU_DATABASE_URL` to Render environment variables
2. Modify `build.sh` to run a migration script (not recommended - often fails due to network restrictions)

## Step 5: Deploy and Test

1. **Deploy**: Render will automatically deploy when you save the configuration
2. **Monitor logs**: Check the build logs and runtime logs for errors
3. **Test the site**: Visit your Render URL (e.g., `https://your-app.onrender.com`)
4. **Test admin**: Visit `/admin` and verify you can log in
5. **Verify data**: Check that your content is present

## Step 6: Update DNS (if using custom domain)

1. In Render Web Service → **Settings** → **Custom Domain**
2. Add your custom domain
3. Update DNS records as instructed by Render
4. Update `WAGTAILADMIN_BASE_URL` to use your custom domain

## Step 7: Post-Migration Tasks

### 7.1 Verify Everything Works

- [ ] Homepage loads correctly
- [ ] Admin panel accessible
- [ ] Media files load (check S3 configuration)
- [ ] Forms work (test contact forms)
- [ ] Email sending works (test with SendGrid)
- [ ] Static files load correctly
- [ ] Database queries work (check content pages)

### 7.2 Security Hardening

1. **Set DEBUG = False** - Now configurable via `DEBUG` environment variable (defaults to `False`)
2. **Update ALLOWED_HOSTS** - Set `ALLOWED_HOSTS` environment variable to your specific domain(s) instead of `['*']`
3. **Review logging levels** - Now configurable via environment variables (defaults to `INFO` for production)
4. **Verify security settings** - Check that `DEBUG=False` and `ALLOWED_HOSTS` is set correctly in Render dashboard

### 7.3 Clean Up

- [ ] Remove `heroku_dump.sql` from your repository (already in `.gitignore`)
- [ ] Remove any temporary environment variables
- [ ] Document any Render-specific configurations

## Step 8: Switch Traffic (if applicable)

1. **Update DNS** to point to Render (if using custom domain)
2. **Monitor** for any issues
3. **Keep Heroku running** for a few days as backup
4. **Export final backup** from Heroku before shutting down

## Troubleshooting

### Build Fails

- Check build logs in Render dashboard
- Verify `build.sh` has execute permissions (`chmod +x build.sh`)
- Ensure all dependencies are in `requirements.txt`

### Database Connection Issues

- Verify `DATABASE_URL` is set (should be automatic when database is linked)
- Check database is running in Render dashboard
- Verify database credentials

### Static Files Not Loading

- Check WhiteNoise is configured (already done in `production.py`)
- Verify `collectstatic` runs in `build.sh` (already configured)
- Check S3 configuration if using S3 for static files

### Media Files Not Loading

- Verify AWS credentials are correct
- Check S3 bucket permissions
- Verify `S3_BUCKET_NAME` matches your bucket

### 500 Errors

- Check Render logs for detailed error messages
- Verify all environment variables are set
- Check `DEBUG = True` temporarily to see error details (remember to turn off!)

## Rollback Plan

If something goes wrong:

1. **Keep Heroku running** until migration is verified
2. **Point DNS back** to Heroku if needed
3. **Review logs** to identify issues
4. **Fix issues** and redeploy to Render

## Additional Resources

- [Render Documentation](https://render.com/docs)
- [Django on Render](https://render.com/docs/deploy-django)
- [PostgreSQL on Render](https://render.com/docs/databases)
- Your existing `MANUAL_MIGRATION.md` for database migration details

## Notes

- Your `build.sh` already handles migrations and static file collection
- Your `Procfile` is compatible with Render
- Your production settings already use `DATABASE_URL` which Render provides automatically
- WhiteNoise is configured for static files (works great on Render)

---

**Estimated Time:** 2-4 hours (depending on database size and complexity)

**Risk Level:** Medium (keep Heroku as backup during transition)
