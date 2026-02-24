"""
Middleware for performance and caching (Pingdom / best practices).
"""


def _is_organization_detail_path(path):
    """
    True if path is an organization detail page (e.g. /organizations-listing/dcp/)
    and not the org index (e.g. /organizations-listing/).
    """
    path = (path or "").strip("/")
    parts = [p for p in path.split("/") if p]
    # Index: /organizations-listing/  -> parts == ['organizations-listing']
    # Detail: /organizations-listing/dcp/ -> parts == ['organizations-listing', 'dcp']
    return (
        len(parts) >= 2
        and parts[0].lower() == "organizations-listing"
    )


class BlockOrganizationDetailMiddleware:
    """
    Return 403 (and noindex) for GET requests to organization detail URLs
    (e.g. /organizations-listing/dcp/) while keeping those pages published.
    Use when you want org pages to stay live and listed but not reachable by
    bots or direct URL traversal. Disable by setting BLOCK_ORGANIZATION_DETAIL_URLS=False.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.conf import settings
        if not getattr(settings, "BLOCK_ORGANIZATION_DETAIL_URLS", True):
            return self.get_response(request)
        if request.method != "GET":
            return self.get_response(request)
        if not _is_organization_detail_path(request.path):
            return self.get_response(request)
        from django.http import HttpResponseForbidden
        response = HttpResponseForbidden(
            "<h1>403 Forbidden</h1><p>This page is not available at this URL.</p>",
            content_type="text/html",
        )
        response["X-Robots-Tag"] = "noindex, nofollow"
        return response


class CacheControlHeadersMiddleware:
    """
    Set Cache-Control on Django-served HTML so browsers and CDNs can cache
    (addresses "Add Expires headers" / F1 in Pingdom).
    Uses a short max-age so content updates still propagate; skip admin and auth.
    """

    # Path prefixes that should not get public cache (admin, auth, etc.)
    SKIP_PREFIXES = ('/admin', '/django-admin', '/en/admin')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.method != 'GET':
            return response
        if response.get('Cache-Control'):
            return response
        content_type = response.get('Content-Type') or ''
        if 'text/html' not in content_type:
            return response
        path = request.path
        if any(path.startswith(p) for p in self.SKIP_PREFIXES):
            return response
        if 200 <= response.status_code < 300:
            response['Cache-Control'] = 'public, max-age=300'
        return response
