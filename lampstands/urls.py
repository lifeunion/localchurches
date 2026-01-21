from django.conf import settings
from django.urls import include, path, re_path
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap

from search import views as search_views
from lampstands.core import urls as lampstands_urls

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.documents.api.v2.views import DocumentsAPIViewSet
from wagtail.images.api.v2.views import ImagesAPIViewSet

api_router = WagtailAPIRouter('wagtailapi')
api_router.register_endpoint('pages', PagesAPIViewSet)
api_router.register_endpoint('images', ImagesAPIViewSet)
api_router.register_endpoint('documents', DocumentsAPIViewSet)

urlpatterns = [
    path('api/v2/', api_router.urls),
    path('django-admin/', admin.site.urls),
    path('testimony-of-Jesus/', include(wagtailadmin_urls)),
    path('documents/', include(wagtaildocs_urls)),
    path('search/', search_views.search, name='search'),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.views.generic import TemplateView

    # Serve static and media files from development server
    # Only add staticfiles_urlpatterns if not using WhiteNoise in production
    # In production with DEBUG=True, we still use WhiteNoise, so skip this
    if not hasattr(settings, 'STORAGES') or settings.STORAGES.get('staticfiles', {}).get('BACKEND') != 'whitenoise.storage.CompressedStaticFilesStorage':
        urlpatterns += staticfiles_urlpatterns()
    # Only serve media files if MEDIA_URL is not within STATIC_URL
    if not settings.MEDIA_URL.startswith(settings.STATIC_URL):
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Add views for testing 404 and 500 templates
    urlpatterns += [
        path('test404/', TemplateView.as_view(template_name='404.html')),
        path('test500/', TemplateView.as_view(template_name='500.html')),
    ]

urlpatterns += [
    re_path(r'', include(lampstands_urls)),
    re_path(r'', include(wagtail_urls)),
]

handler404 = 'lampstands.core.views.error404'
handler500 = 'lampstands.core.views.error500'
