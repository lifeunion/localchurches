#!/bin/bash
# Script to check what version of a file CloudFront is serving
# Compares CloudFront response with S3 direct access

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: ./check_cloudfront_file.sh <cloudfront-url> <s3-path>"
    echo ""
    echo "Examples:"
    echo "  ./check_cloudfront_file.sh https://d1234567890.cloudfront.net/css/villareal-turquoise.css css/villareal-turquoise.css"
    echo "  ./check_cloudfront_file.sh https://cdn.yourdomain.com/css/file.css css/file.css"
    exit 1
fi

CLOUDFRONT_URL="$1"
S3_PATH="$2"
BUCKET="lcstatic"
S3_URL="https://${BUCKET}.s3.us-east-1.amazonaws.com/${S3_PATH}"

echo "=========================================="
echo "CloudFront vs S3 File Comparison"
echo "=========================================="
echo ""

# Get CloudFront file info
echo "📡 CloudFront Response:"
echo "   URL: ${CLOUDFRONT_URL}"
echo ""
CF_HEADERS=$(curl -sI "${CLOUDFRONT_URL}?$(date +%s)" 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "$CF_HEADERS" | grep -E "HTTP|ETag|Last-Modified|Content-Length|Cache-Control|Age|X-Cache" | sed 's/^/   /'
    CF_ETAG=$(echo "$CF_HEADERS" | grep -i "ETag:" | cut -d' ' -f2 | tr -d '\r')
    CF_LAST_MOD=$(echo "$CF_HEADERS" | grep -i "Last-Modified:" | cut -d' ' -f2- | tr -d '\r')
    CF_SIZE=$(echo "$CF_HEADERS" | grep -i "Content-Length:" | cut -d' ' -f2 | tr -d '\r')
    CF_AGE=$(echo "$CF_HEADERS" | grep -i "Age:" | cut -d' ' -f2 | tr -d '\r')
    CF_CACHE=$(echo "$CF_HEADERS" | grep -i "X-Cache:" | cut -d' ' -f2 | tr -d '\r')
else
    echo "   ❌ Error: Could not fetch from CloudFront"
    exit 1
fi

echo ""
echo "📦 S3 Direct Response:"
echo "   URL: ${S3_URL}"
echo ""
S3_HEADERS=$(curl -sI "${S3_URL}?$(date +%s)" 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "$S3_HEADERS" | grep -E "HTTP|ETag|Last-Modified|Content-Length" | sed 's/^/   /'
    S3_ETAG=$(echo "$S3_HEADERS" | grep -i "ETag:" | cut -d' ' -f2 | tr -d '\r"')
    S3_LAST_MOD=$(echo "$S3_HEADERS" | grep -i "Last-Modified:" | cut -d' ' -f2- | tr -d '\r')
    S3_SIZE=$(echo "$S3_HEADERS" | grep -i "Content-Length:" | cut -d' ' -f2 | tr -d '\r')
else
    echo "   ❌ Error: Could not fetch from S3"
    exit 1
fi

echo ""
echo "=========================================="
echo "Comparison:"
echo "=========================================="

# Compare ETags
if [ "$CF_ETAG" = "$S3_ETAG" ]; then
    echo "✅ ETag Match: Files are identical"
    echo "   CloudFront: ${CF_ETAG}"
    echo "   S3:         ${S3_ETAG}"
else
    echo "❌ ETag Mismatch: Files are different!"
    echo "   CloudFront: ${CF_ETAG}"
    echo "   S3:         ${S3_ETAG}"
fi

echo ""

# Compare sizes
if [ "$CF_SIZE" = "$S3_SIZE" ]; then
    echo "✅ Size Match: ${CF_SIZE} bytes"
else
    echo "❌ Size Mismatch:"
    echo "   CloudFront: ${CF_SIZE} bytes"
    echo "   S3:         ${S3_SIZE} bytes"
fi

echo ""

# Check cache status
if [ -n "$CF_CACHE" ]; then
    if [[ "$CF_CACHE" == *"Hit"* ]]; then
        echo "📦 CloudFront Cache: HIT (serving from cache)"
        if [ -n "$CF_AGE" ]; then
            echo "   Age: ${CF_AGE} seconds"
        fi
    else
        echo "📦 CloudFront Cache: MISS (fetched from origin)"
    fi
fi

echo ""

# Compare Last-Modified
if [ -n "$CF_LAST_MOD" ] && [ -n "$S3_LAST_MOD" ]; then
    echo "📅 Last Modified:"
    echo "   CloudFront: ${CF_LAST_MOD}"
    echo "   S3:         ${S3_LAST_MOD}"
fi

echo ""
echo "=========================================="
echo "File Content Preview (first 10 lines):"
echo "=========================================="
echo ""
echo "CloudFront:"
curl -s "${CLOUDFRONT_URL}?$(date +%s)" 2>/dev/null | head -10 | sed 's/^/   /'
echo ""
echo "S3 Direct:"
curl -s "${S3_URL}?$(date +%s)" 2>/dev/null | head -10 | sed 's/^/   /'
