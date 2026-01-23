# Heroku Database Changes Analysis

## Summary

**Good News**: Based on code analysis, **NO scripts have directly modified the Heroku PostgreSQL database** in the past 3 days.

## What Was Changed (All on Render, NOT Heroku)

All database modifications in the past 3 days were made to **Render's PostgreSQL database**, not Heroku:

1. **`fix_userprofile` management command** - Runs during Render builds via `build.sh`
   - Uses Django's `connection` which connects to `DATABASE_URL` (Render's database)
   - Only runs on Render during deployment

2. **`/fix-userprofile/` API endpoint** - Temporary fix endpoint
   - Also uses Django's `connection` → connects to Render's database
   - Only accessible on Render deployment

3. **`fix_database_direct.py`** - Standalone script
   - Takes `DATABASE_URL` as parameter
   - Would only modify Heroku if explicitly passed `HEROKU_DATABASE_URL`
   - No evidence this was run with Heroku credentials

4. **`fix_wagtail_userprofile.py`** - Standalone script
   - Uses Django's `connection` → connects to whatever `DATABASE_URL` is set
   - Would only modify Heroku if run locally with `HEROKU_DATABASE_URL` as `DATABASE_URL`

## Potential Issue Found

**CRITICAL**: `lampstands/settings/base.py` contains **hardcoded Heroku database credentials** (lines 113-121):

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'd85jsi3phqta5n',
        'HOST': 'ec2-54-243-124-240.compute-1.amazonaws.com',
        'PASSWORD': '1edeae694aa4e49354562c4b36fefdc6eded2fc251f9615558b4ce013aa4ba0b',
        'USER': 'iqmxhqvsegcfet',
    }
}
```

**However**, `production.py` (lines 80-89) **overrides** this with `DATABASE_URL` from environment variables, so:
- ✅ **On Render**: Uses Render's database (from `DATABASE_URL` env var)
- ⚠️ **Locally**: Would use Heroku database if `DATABASE_URL` is not set

## Could Heroku Have Been Modified?

**Only if:**
1. Someone ran `fix_database_direct.py` or `fix_wagtail_userprofile.py` **locally** with `HEROKU_DATABASE_URL` set as `DATABASE_URL`
2. Or if someone manually ran SQL against Heroku

**Evidence against Heroku modification:**
- All commits show fixes targeting Render database
- `build.sh` runs on Render, uses Render's `DATABASE_URL`
- No scripts explicitly target Heroku

## Recommendation

1. **Remove hardcoded Heroku credentials** from `base.py` (security risk)
2. **Check Heroku database directly** to verify no columns were added:
   ```sql
   SELECT column_name 
   FROM information_schema.columns 
   WHERE table_name = 'wagtailusers_userprofile'
   ORDER BY column_name;
   ```
3. **If columns were added to Heroku**, they can be removed:
   ```sql
   ALTER TABLE wagtailusers_userprofile 
   DROP COLUMN IF EXISTS updated_comments_notifications,
   DROP COLUMN IF EXISTS rejected_notifications,
   DROP COLUMN IF EXISTS current_time_zone,
   DROP COLUMN IF EXISTS preferred_language,
   DROP COLUMN IF EXISTS avatar,
   DROP COLUMN IF EXISTS dismissibles,
   DROP COLUMN IF EXISTS theme,
   DROP COLUMN IF EXISTS contrast,
   DROP COLUMN IF EXISTS density,
   DROP COLUMN IF EXISTS keyboard_shortcuts;
   ```

## Next Steps

1. Wait for current Render deploy to finish
2. Verify Render database has all columns
3. Check Heroku database schema to confirm no changes
4. Remove hardcoded credentials from `base.py` if confirmed safe
