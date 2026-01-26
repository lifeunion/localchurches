#!/usr/bin/env bash
# Set DJANGO_SETTINGS_MODULE by branch: production for master, staging for others.
# Staging uses WhiteNoise only so lcstatic S3 is never touched.
if [ "${RENDER_GIT_BRANCH:-master}" = "master" ]; then
  export DJANGO_SETTINGS_MODULE=lampstands.settings.production
else
  export DJANGO_SETTINGS_MODULE=lampstands.settings.staging
fi
echo "Starting with DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} (RENDER_GIT_BRANCH=${RENDER_GIT_BRANCH:-master})"

# Ensure staticfiles/ exists at runtime (Render may not persist build output).
# Without this, WhiteNoise sees "No directory at staticfiles/" and /static/* 404s.
# Run collectstatic without --clear to avoid wiping; if staticfiles/ is missing, it is created.
python manage.py collectstatic --no-input --verbosity 0 || true

exec gunicorn lampstands.wsgi --log-file -
