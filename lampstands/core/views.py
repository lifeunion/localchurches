import requests
import logging

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
from rest_framework import status

logger = logging.getLogger(__name__)


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
    
    # Always return a response - render the 500 template for production
    return render(request, '500.html', status=500)


@api_view(['GET'])
def fix_userprofile(request):
    """
    One-time fix endpoint to add missing userprofile columns for Wagtail 6.4.
    TEMPORARY: No auth required for quick fix - REMOVE AFTER USE
    """
    from django.db import connection
    
    # List of all columns that Wagtail 6.4 expects
    columns_to_add = [
        {
            'name': 'updated_comments_notifications',
            'type': 'BOOLEAN',
            'default': 'FALSE',
            'null': 'NOT NULL'
        },
        {
            'name': 'rejected_notifications',
            'type': 'BOOLEAN',
            'default': 'FALSE',
            'null': 'NOT NULL'
        },
        {
            'name': 'current_time_zone',
            'type': 'VARCHAR(40)',
            'default': "''",
            'null': 'NOT NULL'
        },
        {
            'name': 'preferred_language',
            'type': 'VARCHAR(10)',
            'default': "''",
            'null': 'NOT NULL'
        },
        {
            'name': 'avatar_id',
            'type': 'INTEGER',
            'default': 'NULL',
            'null': 'NULL',
            'note': 'ForeignKey to wagtailimages.Image - nullable'
        },
    ]
    
    try:
        with connection.cursor() as cursor:
            added_columns = []
            existing_columns = []
            
            for col in columns_to_add:
                # Check if column exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = 'wagtailusers_userprofile'
                        AND column_name = %s
                    );
                """, [col['name']])
                
                column_exists = cursor.fetchone()[0]
                
                if not column_exists:
                    # Build ALTER TABLE statement
                    null_clause = col['null'] if col.get('null') else 'NOT NULL'
                    default_clause = f"DEFAULT {col['default']}" if col.get('default') else ''
                    alter_sql = f"""
                        ALTER TABLE wagtailusers_userprofile 
                        ADD COLUMN {col['name']} {col['type']} {default_clause} {null_clause};
                    """
                    cursor.execute(alter_sql)
                    added_columns.append(col['name'])
                else:
                    existing_columns.append(col['name'])
            
            if added_columns:
                return Response({
                    'status': 'success',
                    'message': f'Added {len(added_columns)} column(s)',
                    'added': added_columns,
                    'existing': existing_columns
                })
            else:
                return Response({
                    'status': 'already_exists',
                    'message': 'All columns already exist',
                    'existing': existing_columns
                })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)


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
    serializer_class = LocalitiesSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    
    def get_queryset(self):
        """
        Filter to only include live churches with valid position data.
        Position is stored as "lat,lng" string, so we check for non-null, non-empty, and contains comma.
        Optimized to avoid multiple count queries and filter invalid data before serialization.
        
        Performance optimizations:
        - Use values() to get dicts instead of model instances (much faster, less memory)
        - Only fetch fields needed by serializer
        - NOTE: Using values() avoids model instance overhead and is significantly faster
        """
        # Use values() to get dicts instead of model instances - much faster!
        # This avoids model instance creation overhead and reduces memory usage
        queryset = ChurchPage.objects.filter(
            live=True,
            position__isnull=False
        ).exclude(
            position=''
        ).filter(
            position__contains=','
        ).values(
            'id',
            'slug',
            'locality_name',
            'meeting_address',
            'locality_state_or_province',
            'locality_country',
            'locality_phone_number',
            'locality_email',
            'locality_web',
            'position',
            'locality_contact_brother_1',
            'locality_contact_brother_1_phone',
            'locality_contact_brother_2',
            'locality_contact_brother_2_phone',
            'locality_contact_brother_3',
            'locality_contact_brother_3_phone',
            'locality_contact_brother_4',
            'locality_contact_brother_4_phone',
            'locality_contact_brother_5',
            'locality_contact_brother_5_phone',
            'locality_contact_brother_6',
            'locality_contact_brother_6_phone',
        ).order_by('id')
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """
        Override list method with performance diagnostics and response caching.
        URLs are built from slug only in serializer (no get_url_parts/url) to avoid N+1 queries.
        Response data is cached for 60 minutes to dramatically improve performance for repeated requests.
        """
        import time
        import hashlib
        from django.db import connection
        from django.db import reset_queries
        from django.core.cache import cache
        from rest_framework.response import Response
        
        reset_queries()
        start_time = time.time()
        
        # Create cache key based on request parameters
        cache_key = f'localities_list_{hashlib.md5(str(request.GET.urlencode()).encode()).hexdigest()}'
        
        # Try to get cached response data
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"[LocalitiesList] Cache HIT - returning cached response")
            record_count = len(cached_data) if isinstance(cached_data, list) else 0
            logger.warning(f"[LocalitiesList] Cached: {record_count} records, 0 queries, <0.01s total")
            return Response(cached_data)
        
        logger.info(f"[LocalitiesList] Cache MISS - generating response")
        
        response = super().list(request, *args, **kwargs)
        
        # Get record count from response data (avoids extra count() query)
        record_count = len(response.data) if hasattr(response, 'data') and isinstance(response.data, list) else 0
        
        end_time = time.time()
        query_count = len(connection.queries)
        total_time = end_time - start_time
        per_record = (total_time / record_count * 1000) if record_count > 0 else 0
        
        logger.warning(
            f"[LocalitiesList] Performance: {record_count} records, "
            f"{query_count} queries, {total_time:.2f}s total, {per_record:.2f}ms per record"
        )
        if query_count > 50:
            logger.warning(f"[LocalitiesList] High query count: {query_count}")
        
        # Cache the response data for 60 minutes (3600 seconds)
        # Church data doesn't change frequently, so this is safe
        if hasattr(response, 'data'):
            cache.set(cache_key, response.data, 3600)
            logger.info(f"[LocalitiesList] Response cached for 60 minutes")
        
        return response


class LocalitiesDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ChurchPage.objects.all()
    serializer_class = LocalitiesSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
