#!/usr/bin/env bash
# Usage: CLOUDFRONT_STATIC_URL=https://d24pmr7604s8mt.cloudfront.net ./scripts/warm_cloudfront.sh
# Run after deploy or after invalidation. Warms POP(s) near this machine.

set -e
BASE="${CLOUDFRONT_STATIC_URL:?Set CLOUDFRONT_STATIC_URL to your CloudFront URL, e.g. https://d24pmr7604s8mt.cloudfront.net}"
PATHS=(
  /wagtailadmin/css/core.css
  /wagtailadmin/js/common.js
  /wagtailadmin/js/wagtailadmin.js
  /wagtailadmin/js/core.js
)
for p in "${PATHS[@]}"; do
  echo "Warming $BASE$p"
  curl -sS -o /dev/null -w "%{http_code} %{url_effective}\n" "$BASE$p"
done
echo "Done. POP(s) near this host are warmed."
