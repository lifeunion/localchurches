#!/usr/bin/env bash
# Run from project root (Render runs from repo root; ensure we can find manage.py)
cd "$(dirname "$0")/.." || true

# Set DJANGO_SETTINGS_MODULE by branch: production for master, staging for others.
# Staging uses WhiteNoise only so lcstatic S3 is never touched.
if [ "${RENDER_GIT_BRANCH:-master}" = "master" ]; then
  export DJANGO_SETTINGS_MODULE=lampstands.settings.production
else
  export DJANGO_SETTINGS_MODULE=lampstands.settings.staging
fi
echo "Starting with DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} (RENDER_GIT_BRANCH=${RENDER_GIT_BRANCH:-master})"

# Ensure staticfiles/ exists and contains our static files. Render may not persist
# build output, and collectstatic can fail at runtime (e.g. DB/imports). Copy the
# repo's static/ into staticfiles/ first so WhiteNoise can serve css/, js/, etc.
mkdir -p staticfiles
if [ -d "static" ]; then
  echo "Copying static/ into staticfiles/..."
  cp -r static/* staticfiles/ 2>/dev/null || true
fi
python manage.py collectstatic --no-input --verbosity 1 2>&1 | tail -5 || true

exec gunicorn lampstands.wsgi --log-file -
