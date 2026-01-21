#!/usr/bin/env python3
"""
Fix Wagtail site configuration after migration.
This script ensures the site root page is configured correctly.
"""
import os
import sys
import django

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lampstands.settings.production')
django.setup()

from wagtail.models import Site, Page

def main():
    print("=" * 60)
    print("Fixing Wagtail Site Configuration")
    print("=" * 60)
    
    # Get the default site or create one
    try:
        site = Site.objects.get(is_default_site=True)
        print(f"Found default site: {site.hostname}:{site.port}")
    except Site.DoesNotExist:
        print("No default site found. Creating one...")
        # Get the root page
        try:
            root_page = Page.objects.filter(depth=1).first()
            if not root_page:
                print("ERROR: No root page found!")
                return 1
            
            site = Site.objects.create(
                hostname='localchurches.onrender.com',
                port=80,
                site_name='Local Churches',
                root_page=root_page,
                is_default_site=True
            )
            print(f"Created default site: {site.hostname}:{site.port}")
        except Exception as e:
            print(f"ERROR creating site: {e}")
            return 1
    
    # Check if root page is set
    if not site.root_page:
        print("WARNING: Site has no root page!")
        # Find the home page
        try:
            from lampstands.core.models import HomePage
            home_page = HomePage.objects.live().first()
            if home_page:
                print(f"Found home page: {home_page.title} (ID: {home_page.id})")
                site.root_page = home_page
                site.save()
                print(f"✓ Set root page to: {home_page.title}")
            else:
                # Get any page as root
                root_page = Page.objects.filter(depth=1).first()
                if root_page:
                    site.root_page = root_page
                    site.save()
                    print(f"✓ Set root page to: {root_page.title}")
                else:
                    print("ERROR: No pages found!")
                    return 1
        except Exception as e:
            print(f"ERROR setting root page: {e}")
            return 1
    else:
        print(f"✓ Root page is set: {site.root_page.title} (ID: {site.root_page.id})")
    
    # List all pages
    print("\nPages in database:")
    pages = Page.objects.all().order_by('depth', 'path')
    for page in pages[:20]:  # Show first 20
        print(f"  - {page.title} (ID: {page.id}, depth: {page.depth}, path: {page.path})")
    
    if pages.count() > 20:
        print(f"  ... and {pages.count() - 20} more pages")
    
    print(f"\n✓ Site configuration complete!")
    print(f"  Site: {site.hostname}:{site.port}")
    print(f"  Root Page: {site.root_page.title if site.root_page else 'NOT SET'}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
