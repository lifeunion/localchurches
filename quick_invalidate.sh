#!/bin/bash
# Quick script to invalidate CloudFront cache for villareal-turquoise.css

if [ -z "$1" ]; then
    echo "Usage: ./quick_invalidate.sh <cloudfront-distribution-id>"
    echo ""
    echo "Example:"
    echo "  ./quick_invalidate.sh E1234567890ABC"
    echo ""
    echo "To find your distribution ID:"
    echo "  aws cloudfront list-distributions --output table | grep lcstatic"
    exit 1
fi

DISTRIBUTION_ID="$1"
FILE_PATH="/css/villareal-turquoise.css"

echo "Creating CloudFront invalidation..."
echo "  Distribution ID: $DISTRIBUTION_ID"
echo "  Path: $FILE_PATH"
echo ""

# Check if AWS CLI is available
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Install it first:"
    echo "   brew install awscli  # macOS"
    echo "   or: pip install awscli"
    echo ""
    echo "Or use AWS Console:"
    echo "   https://console.aws.amazon.com/cloudfront/"
    exit 1
fi

# Create invalidation
RESULT=$(aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "$FILE_PATH" \
  --output json 2>&1)

if [ $? -eq 0 ]; then
    INVALIDATION_ID=$(echo "$RESULT" | grep -o '"Id":"[^"]*"' | cut -d'"' -f4)
    echo "✅ Invalidation created successfully!"
    echo "   Invalidation ID: $INVALIDATION_ID"
    echo ""
    echo "⏳ Invalidation typically takes 1-5 minutes to complete."
    echo "   Check status:"
    echo "   aws cloudfront get-invalidation --distribution-id $DISTRIBUTION_ID --id $INVALIDATION_ID"
else
    echo "❌ Error creating invalidation:"
    echo "$RESULT"
    exit 1
fi
