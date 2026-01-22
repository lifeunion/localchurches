#!/usr/bin/env python3
"""
Diagnostic script to check migration status and database state.
Run this to see what data was actually migrated.
"""
import os
import sys
import django

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lampstands.settings.production')
django.setup()

from django.db import connection
from wagtail.models import Site, Page

def main():
    print("=" * 60)
    print("Migration Status Check")
    print("=" * 60)
    
    with connection.cursor() as cursor:
        # Check revisions
        cursor.execute("SELECT COUNT(*) FROM wagtailcore_revision")
        rev_count = cursor.fetchone()[0]
        print(f"\n1. Revisions:")
        print(f"   Total: {rev_count}")
        
        # Check pages
        cursor.execute("SELECT COUNT(*) FROM wagtailcore_page")
        page_count = cursor.fetchone()[0]
        print(f"\n2. Pages:")
        print(f"   Total: {page_count}")
        
        # Check for HomePage
        cursor.execute("""
            SELECT COUNT(*) FROM wagtailcore_page p
            JOIN django_content_type ct ON p.content_type_id = ct.id
            WHERE ct.app_label = 'lampstands' AND ct.model = 'homepage'
        """)
        homepage_count = cursor.fetchone()[0]
        print(f"   HomePage instances: {homepage_count}")
        
        # List all page types
        cursor.execute("""
            SELECT ct.app_label, ct.model, COUNT(*) as count
            FROM wagtailcore_page p
            JOIN django_content_type ct ON p.content_type_id = ct.id
            GROUP BY ct.app_label, ct.model
            ORDER BY count DESC
        """)
        page_types = cursor.fetchall()
        print(f"\n   Page types breakdown:")
        for app_label, model, count in page_types[:10]:
            print(f"     - {app_label}.{model}: {count}")
        
        # Check sites
        cursor.execute("SELECT COUNT(*) FROM wagtailcore_site")
        site_count = cursor.fetchone()[0]
        print(f"\n3. Sites:")
        print(f"   Total: {site_count}")
        
        # Check site configuration
        cursor.execute("""
            SELECT id, hostname, port, root_page_id, is_default_site
            FROM wagtailcore_site
        """)
        sites = cursor.fetchall()
        for site_id, hostname, port, root_page_id, is_default in sites:
            print(f"   Site {site_id}: {hostname}:{port}")
            print(f"     Default: {is_default}")
            print(f"     Root page ID: {root_page_id}")
            if root_page_id:
                cursor.execute("SELECT title, depth, path FROM wagtailcore_page WHERE id = %s", [root_page_id])
                page_info = cursor.fetchone()
                if page_info:
                    print(f"     Root page: {page_info[0]} (depth: {page_info[1]}, path: {page_info[2]})")
                else:
                    print(f"     ⚠ Root page {root_page_id} does not exist!")
    
    # Use Django ORM to check
    print(f"\n4. Django ORM Check:")
    try:
        site = Site.objects.get(is_default_site=True)
        print(f"   Default site: {site.hostname}:{site.port}")
        if site.root_page:
            print(f"   Root page: {site.root_page.title} (ID: {site.root_page.id})")
            print(f"   Root page type: {site.root_page.content_type.app_label}.{site.root_page.content_type.model}")
            print(f"   Root page live: {site.root_page.live}")
        else:
            print(f"   ⚠ No root page set!")
    except Site.DoesNotExist:
        print(f"   ⚠ No default site found!")
    
    # Check for HomePage using ORM
    try:
        from lampstands.core.models import HomePage
        home_pages = HomePage.objects.all()
        print(f"\n5. HomePage Check (ORM):")
        print(f"   Total HomePage instances: {home_pages.count()}")
        for hp in home_pages[:5]:
            print(f"     - {hp.title} (ID: {hp.id}, live: {hp.live}, depth: {hp.depth})")
    except Exception as e:
        print(f"   Error checking HomePage: {e}")
    
    # Check page tree structure
    print(f"\n6. Page Tree Structure:")
    root_pages = Page.objects.filter(depth=1)
    print(f"   Root level pages (depth=1): {root_pages.count()}")
    for page in root_pages[:5]:
        print(f"     - {page.title} (ID: {page.id}, path: {page.path})")
        children = page.get_children()
        print(f"       Children: {children.count()}")
    
    print(f"\n" + "=" * 60)
    print("Diagnostic complete!")
    print("=" * 60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
