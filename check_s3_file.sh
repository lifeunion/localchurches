#!/bin/bash
# Quick script to check if a file exists in S3 and show its metadata

if [ -z "$1" ]; then
    echo "Usage: ./check_s3_file.sh <s3-path>"
    echo "Example: ./check_s3_file.sh static/css/villareal-turquoise.css"
    exit 1
fi

FILE_PATH="$1"
BUCKET="lcstatic"

echo "Checking S3 file: s3://${BUCKET}/${FILE_PATH}"
echo ""

# Check if file exists
if aws s3 ls "s3://${BUCKET}/${FILE_PATH}" 2>/dev/null; then
    echo ""
    echo "✅ File exists in S3"
    echo ""
    
    # Get file metadata
    echo "File metadata:"
    aws s3api head-object --bucket "$BUCKET" --key "$FILE_PATH" 2>/dev/null | \
        jq -r '. | "  Size: \(.ContentLength) bytes\n  Last Modified: \(.LastModified)\n  ETag: \(.ETag)\n  Content Type: \(.ContentType)"' 2>/dev/null || \
        aws s3api head-object --bucket "$BUCKET" --key "$FILE_PATH" 2>/dev/null
    
    echo ""
    echo "Direct S3 URL:"
    echo "https://${BUCKET}.s3.amazonaws.com/${FILE_PATH}"
    echo ""
    echo "To view file content:"
    echo "aws s3 cp s3://${BUCKET}/${FILE_PATH} - | head -50"
else
    echo "❌ File NOT found in S3"
    echo ""
    echo "Listing similar files:"
    DIR=$(dirname "$FILE_PATH")
    aws s3 ls "s3://${BUCKET}/${DIR}/" --recursive 2>/dev/null | grep -i "$(basename "$FILE_PATH")" | head -10
fi
