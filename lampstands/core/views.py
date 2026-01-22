import requests

from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse, Http404

from .models import ChurchPage
from .serializers import LocalitiesSerializer

from rest_framework import generics
from rest_framework import permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


def error404(request, exception=None):
    if '/play/' in request.path:
        return render(request, 'play_404.html', {'play_404': True}, status=404)
    else:
        return render(request, '404.html', status=404)


def error500(request):
    """Custom 500 error handler that logs the error"""
    import traceback
    import sys
    import logging
    
    logger = logging.getLogger('django.request')
    
    # Get the exception info if available
    exc_type, exc_value, exc_traceback = sys.exc_info()
    if exc_type:
        logger.error(
            "Internal Server Error: %s",
            exc_value,
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        # Also print to console for immediate visibility
        traceback.print_exception(exc_type, exc_value, exc_traceback)
    
    # If DEBUG is True, let Django handle it with the debug page
    if settings.DEBUG:
        from django.views.debug import technical_500_response
        return technical_500_response(request, *sys.exc_info())
    
    # Otherwise render the 500.html template
    return render(request, '500.html', status=500)


def diagnostic_view(request):
    """Diagnostic endpoint to check database migration status"""
    from django.db import connection
    from wagtail.models import Site, Page
    import json
    
    output = []
    homepage_count = 0
    output.append("=" * 60)
    output.append("Database Migration Diagnostic")
    output.append("=" * 60)
    output.append("")
    
    with connection.cursor() as cursor:
        # Check revisions
        cursor.execute("SELECT COUNT(*) FROM wagtailcore_revision")
        rev_count = cursor.fetchone()[0]
        output.append(f"1. Revisions: {rev_count}")
        
        # Check pages
        cursor.execute("SELECT COUNT(*) FROM wagtailcore_page")
        page_count = cursor.fetchone()[0]
        output.append(f"2. Pages: {page_count}")
        
        # Check for HomePage
        cursor.execute("""
            SELECT COUNT(*) FROM wagtailcore_page p
            JOIN django_content_type ct ON p.content_type_id = ct.id
            WHERE ct.app_label = 'lampstands' AND ct.model = 'homepage'
        """)
        homepage_count = cursor.fetchone()[0]
        output.append(f"   HomePage instances: {homepage_count}")
        
        # List all page types
        cursor.execute("""
            SELECT ct.app_label, ct.model, COUNT(*) as count
            FROM wagtailcore_page p
            JOIN django_content_type ct ON p.content_type_id = ct.id
            GROUP BY ct.app_label, ct.model
            ORDER BY count DESC
        """)
        page_types = cursor.fetchall()
        output.append(f"\n   Page types breakdown:")
        for app_label, model, count in page_types[:10]:
            output.append(f"     - {app_label}.{model}: {count}")
        
        # Check sites
        cursor.execute("SELECT COUNT(*) FROM wagtailcore_site")
        site_count = cursor.fetchone()[0]
        output.append(f"\n3. Sites: {site_count}")
        
        # Check site configuration
        cursor.execute("""
            SELECT id, hostname, port, root_page_id, is_default_site
            FROM wagtailcore_site
        """)
        sites = cursor.fetchall()
        for site_id, hostname, port, root_page_id, is_default in sites:
            output.append(f"   Site {site_id}: {hostname}:{port}")
            output.append(f"     Default: {is_default}")
            output.append(f"     Root page ID: {root_page_id}")
            if root_page_id:
                cursor.execute("""
                    SELECT p.title, p.depth, p.path, p.live, ct.app_label, ct.model
                    FROM wagtailcore_page p
                    JOIN django_content_type ct ON p.content_type_id = ct.id
                    WHERE p.id = %s
                """, [root_page_id])
                page_info = cursor.fetchone()
                if page_info:
                    title, depth, path, live, app_label, model = page_info
                    output.append(f"     Root page: '{title}' (ID: {root_page_id})")
                    output.append(f"       Type: {app_label}.{model}")
                    output.append(f"       Depth: {depth}, Path: {path}, Live: {live}")
                    if app_label != 'lampstands' or model != 'homepage':
                        output.append(f"       ⚠ WARNING: Root page is NOT a HomePage!")
                else:
                    output.append(f"     ⚠ Root page {root_page_id} does not exist!")
        
        # Check pages with IDs 1 and 2
        output.append(f"\n4. Pages with IDs 1 and 2:")
        cursor.execute("""
            SELECT p.id, p.title, p.depth, p.path, p.live, ct.app_label, ct.model
            FROM wagtailcore_page p
            JOIN django_content_type ct ON p.content_type_id = ct.id
            WHERE p.id IN (1, 2)
            ORDER BY p.id
        """)
        for page_id, title, depth, path, live, app_label, model in cursor.fetchall():
            output.append(f"   Page {page_id}: '{title}'")
            output.append(f"     Type: {app_label}.{model}, Depth: {depth}, Path: {path}, Live: {live}")
    
    # Use Django ORM to check
    output.append(f"\n5. Django ORM Check:")
    try:
        site = Site.objects.get(is_default_site=True)
        output.append(f"   Default site: {site.hostname}:{site.port}")
        if site.root_page:
            output.append(f"   Root page: {site.root_page.title} (ID: {site.root_page.id})")
            output.append(f"   Root page type: {site.root_page.content_type.app_label}.{site.root_page.content_type.model}")
            output.append(f"   Root page live: {site.root_page.live}")
        else:
            output.append(f"   ⚠ No root page set!")
    except Site.DoesNotExist:
        output.append(f"   ⚠ No default site found!")
    
    # Check for HomePage using ORM
    try:
        from lampstands.core.models import HomePage
        home_pages = HomePage.objects.all()
        output.append(f"\n6. HomePage Check (ORM):")
        output.append(f"   Total HomePage instances: {home_pages.count()}")
        for hp in home_pages[:5]:
            output.append(f"     - {hp.title} (ID: {hp.id}, live: {hp.live}, depth: {hp.depth})")
    except Exception as e:
        output.append(f"   Error checking HomePage: {e}")
    
    output.append("")
    output.append("=" * 60)
    if homepage_count == 0:
        output.append("→ Migration did not copy data. See MANUAL_MIGRATION.md for manual pg_dump/psql steps.")
    output.append("=" * 60)
    
    # Return as plain text
    return HttpResponse('\n'.join(output), content_type='text/plain')


@api_view(['GET', 'POST'])
def api_root(request, format=None):
    context = {'request': request}
    return Response({
        'localities': reverse('snippet-list', request=request, format=format)
    })


class LocalitiesList(generics.ListCreateAPIView):
    queryset = ChurchPage.objects.all()
    serializer_class = LocalitiesSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class LocalitiesDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ChurchPage.objects.all()
    serializer_class = LocalitiesSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
