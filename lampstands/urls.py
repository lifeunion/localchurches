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
    path('fix-userprofile/', lampstands.core.views.fix_userprofile, name='fix_userprofile'),
]

if settings.DEBUG:
    from django.views.generic import TemplateView
    # Don't add static file serving in production even with DEBUG=True
    # WhiteNoise handles static files, and we don't want to serve media files
    # through Django's development server in production

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
