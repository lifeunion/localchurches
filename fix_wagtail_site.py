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

def main(recursion_depth=0):
    if recursion_depth > 1:
        print("ERROR: Too many recursion attempts in fix_wagtail_site.py")
        return 1
        
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
    
    # Check if root page is set and is valid
    if not site.root_page:
        print("WARNING: Site has no root page!")
        # Find the home page - try live first, then any HomePage
        try:
            from lampstands.core.models import HomePage
            home_page = HomePage.objects.live().first()
            if not home_page:
                # Try non-live pages too
                home_page = HomePage.objects.first()
            
            if home_page:
                print(f"Found home page: {home_page.title} (ID: {home_page.id}, live: {home_page.live})")
                site.root_page = home_page
                site.save()
                print(f"✓ Set root page to: {home_page.title}")
            else:
                # Get any page as root (prefer depth=1, but take any page)
                root_page = Page.objects.filter(depth=1).first()
                if not root_page:
                    root_page = Page.objects.exclude(depth=1).first()
                
                if root_page:
                    print(f"Found page to use as root: {root_page.title} (ID: {root_page.id}, depth: {root_page.depth})")
                    site.root_page = root_page
                    site.save()
                    print(f"✓ Set root page to: {root_page.title}")
                else:
                    print("ERROR: No pages found in database!")
                    return 1
        except Exception as e:
            print(f"ERROR setting root page: {e}")
            import traceback
            traceback.print_exc()
            return 1
    else:
        # Verify the root page still exists
        try:
            site.root_page.refresh_from_db()
            print(f"✓ Root page is set: {site.root_page.title} (ID: {site.root_page.id})")
        except Exception as e:
            print(f"WARNING: Root page {site.root_page_id} no longer exists: {e}")
            # Try to find a new root page
            site.root_page = None
            site.save()
            # Recursively call the fix logic (with depth check)
            return main(recursion_depth + 1)
    
    # List all pages
    print("\nPages in database:")
    pages = Page.objects.all().order_by('depth', 'path')
    page_count = pages.count()
    print(f"Total pages found: {page_count}")
    
    if page_count == 0:
        print("⚠ WARNING: No pages found in database!")
        print("This means the migration didn't copy Wagtail pages.")
        print("The site will show the default Wagtail welcome page.")
        return 1
    
    for page in pages[:20]:  # Show first 20
        print(f"  - {page.title} (ID: {page.id}, depth: {page.depth}, path: {page.path})")
    
    if page_count > 20:
        print(f"  ... and {page_count - 20} more pages")
    
    print(f"\n✓ Site configuration complete!")
    print(f"  Site: {site.hostname}:{site.port}")
    print(f"  Root Page: {site.root_page.title if site.root_page else 'NOT SET'}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
