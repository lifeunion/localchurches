"""
Middleware for performance and caching (Pingdom / best practices).
"""


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
