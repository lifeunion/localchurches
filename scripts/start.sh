#!/usr/bin/env bash
# Set DJANGO_SETTINGS_MODULE by branch: production for master, staging for others.
# Staging uses WhiteNoise only so lcstatic S3 is never touched.
if [ "${RENDER_GIT_BRANCH:-master}" = "master" ]; then
  export DJANGO_SETTINGS_MODULE=lampstands.settings.production
else
  export DJANGO_SETTINGS_MODULE=lampstands.settings.staging
fi
echo "Starting with DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} (RENDER_GIT_BRANCH=${RENDER_GIT_BRANCH:-master})"
exec gunicorn lampstands.wsgi --log-file -
