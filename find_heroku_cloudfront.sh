#!/bin/bash
# Script to help find Heroku's CloudFront distribution

echo "Finding CloudFront distribution for Heroku..."
echo ""

# Method 1: Check HTML source for CloudFront URLs
echo "Method 1: Checking HTML source for CloudFront URLs..."
CF_URLS=$(curl -s https://www.localchurches.org 2>/dev/null | grep -o 'https://[^"]*\.cloudfront\.net[^"]*' | head -5)

if [ -n "$CF_URLS" ]; then
    echo "✅ Found CloudFront URLs in HTML:"
    echo "$CF_URLS" | head -1
    CF_DOMAIN=$(echo "$CF_URLS" | head -1 | sed 's|https://\([^/]*\).*|\1|')
    echo ""
    echo "CloudFront domain: $CF_DOMAIN"
    echo ""
    echo "To find Distribution ID, run:"
    echo "  aws cloudfront list-distributions --output table | grep $CF_DOMAIN"
else
    echo "❌ No CloudFront URLs found in HTML"
    echo "   Heroku might be using direct S3 or a different CDN"
fi

echo ""
echo "Method 2: Checking static file URLs..."
STATIC_URLS=$(curl -s https://www.localchurches.org 2>/dev/null | grep -o 'https://[^"]*\.css\|https://[^"]*\.js' | head -5)

if [ -n "$STATIC_URLS" ]; then
    echo "Static file URLs found:"
    echo "$STATIC_URLS"
    echo ""
    FIRST_URL=$(echo "$STATIC_URLS" | head -1)
    if [[ "$FIRST_URL" == *"cloudfront.net"* ]]; then
        echo "✅ Using CloudFront"
    elif [[ "$FIRST_URL" == *"s3.amazonaws.com"* ]]; then
        echo "⚠️  Using direct S3 (no CloudFront detected)"
    else
        echo "⚠️  Using unknown CDN/domain: $(echo "$FIRST_URL" | sed 's|https://\([^/]*\).*|\1|')"
    fi
fi

echo ""
echo "Method 3: List all CloudFront distributions..."
if command -v aws &> /dev/null; then
    echo "Listing distributions with lcstatic origin:"
    aws cloudfront list-distributions \
      --query "DistributionList.Items[?Origins.Items[0].DomainName=='lcstatic.s3.amazonaws.com'].[Id,DomainName,Status,Comment]" \
      --output table 2>/dev/null || echo "❌ AWS CLI not configured or no distributions found"
else
    echo "❌ AWS CLI not installed. Install with: brew install awscli"
fi
