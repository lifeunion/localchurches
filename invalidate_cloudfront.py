#!/usr/bin/env python3
"""
CloudFront Cache Invalidation Script

Usage:
    python invalidate_cloudfront.py /path/to/file.css
    python invalidate_cloudfront.py /static/css/* /static/js/*
    
Environment Variables:
    CLOUDFRONT_DISTRIBUTION_ID - Your CloudFront distribution ID
    AWS_ACCESS_KEY_ID - Your AWS access key (or use AWS CLI credentials)
    AWS_SECRET_ACCESS_KEY - Your AWS secret key (or use AWS CLI credentials)
"""

import boto3
import sys
import os
import time

def invalidate_cache(distribution_id, paths):
    """Invalidate CloudFront cache for given paths."""
    try:
        client = boto3.client('cloudfront')
        
        response = client.create_invalidation(
            DistributionId=distribution_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': len(paths),
                    'Items': paths
                },
                'CallerReference': f'invalidation-{int(time.time())}'
            }
        )
        
        invalidation_id = response['Invalidation']['Id']
        status = response['Invalidation']['Status']
        
        print(f"✅ Invalidation created successfully!")
        print(f"   Distribution ID: {distribution_id}")
        print(f"   Invalidation ID: {invalidation_id}")
        print(f"   Status: {status}")
        print(f"   Paths: {', '.join(paths)}")
        print(f"\n⏳ Invalidation typically takes 1-5 minutes to propagate globally.")
        print(f"   You can check status in AWS Console: https://console.aws.amazon.com/cloudfront/")
        
        return response
    except Exception as e:
        print(f"❌ Error creating invalidation: {e}")
        print(f"\nTroubleshooting:")
        print(f"1. Check AWS credentials are configured")
        print(f"2. Verify distribution ID is correct")
        print(f"3. Ensure you have CloudFront invalidation permissions")
        return None

if __name__ == '__main__':
    # Get distribution ID from environment or command line
    distribution_id = os.environ.get('CLOUDFRONT_DISTRIBUTION_ID')
    
    if len(sys.argv) < 2:
        print("Usage: python invalidate_cloudfront.py <path1> [path2] [path3] ...")
        print("\nExamples:")
        print("  python invalidate_cloudfront.py /static/css/file.css")
        print("  python invalidate_cloudfront.py /static/css/* /static/js/*")
        print("  python invalidate_cloudfront.py /*  # Invalidates everything (expensive!)")
        print("\nEnvironment Variables:")
        print("  CLOUDFRONT_DISTRIBUTION_ID - Your CloudFront distribution ID")
        print("  AWS_ACCESS_KEY_ID - AWS access key (optional if using AWS CLI credentials)")
        print("  AWS_SECRET_ACCESS_KEY - AWS secret key (optional if using AWS CLI credentials)")
        sys.exit(1)
    
    if not distribution_id:
        print("❌ Error: CLOUDFRONT_DISTRIBUTION_ID environment variable not set")
        print("\nSet it with:")
        print("  export CLOUDFRONT_DISTRIBUTION_ID=YOUR_DISTRIBUTION_ID")
        print("\nOr find your distribution ID in AWS Console:")
        print("  https://console.aws.amazon.com/cloudfront/")
        sys.exit(1)
    
    paths = sys.argv[1:]
    
    # Warn if invalidating everything
    if paths == ['/*']:
        print("⚠️  WARNING: You're invalidating everything (/*)")
        print("   This counts as 1 path but invalidates all cached content.")
        print("   First 1,000 paths/month are free, then $0.005 per path.")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            sys.exit(0)
    
    invalidate_cache(distribution_id, paths)
