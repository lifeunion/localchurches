from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.conf.urls import include,url
from django.contrib import admin

from search import views as search_views
from wagtail.contrib.wagtailsitemaps.views import sitemap
from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtailcore import urls as wagtail_urls
from wagtail.wagtaildocs import urls as wagtaildocs_urls
from lampstands.core import urls as lampstands_urls

from wagtail.contrib.wagtailapi import urls as wagtailapi_urls
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.api.v2.endpoints import PagesAPIEndpoint
from wagtail.wagtaildocs.api.v2.endpoints import DocumentsAPIEndpoint
from wagtail.wagtailimages.api.v2.endpoints import ImagesAPIEndpoint

api = WagtailAPIRouter('api')
api.register_endpoint('pages', PagesAPIEndpoint)
api.register_endpoint('images', ImagesAPIEndpoint)
api.register_endpoint('documents', DocumentsAPIEndpoint)

urlpatterns = [
    url(r'^api/', include(wagtailapi_urls)),
    url(r'^api/v2/', include(api.urls)),
    url(r'^django-admin/', include(admin.site.urls)),
    url(r'^admin/', include(wagtailadmin_urls)),
    url(r'^documents/', include(wagtaildocs_urls)),
    url(r'^sitemap\.xml$', sitemap),
    url(r'^search/$', search_views.search, name='search'),

    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:

    # Alternatively, if you want Wagtail pages to be served from a subpath
    # of your site, rather than the site root:
    #    url(r'^pages/', include(wagtail_urls)),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.views.generic import TemplateView, RedirectView

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Add views for testing 404 and 500 templates
    urlpatterns += [
        url(r'^test404/$', TemplateView.as_view(template_name='404.html')),
        url(r'^test500/$', TemplateView.as_view(template_name='500.html')),
    ]

urlpatterns += [
    url(r'', include(lampstands_urls)),
    url(r'', include(wagtail_urls)),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = 'lampstands.core.views.error404'