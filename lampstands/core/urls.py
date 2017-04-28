from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.urlpatterns import format_suffix_patterns
from lampstands.core import views
from django.conf.urls import include
from .views import LocalitiesList, LocalitiesDetail

from django.contrib import admin
from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtaildocs import urls as wagtaildocs_urls
from wagtail.wagtailcore import urls as wagtail_urls
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
	url(r'^api-localities/$', views.LocalitiesList.as_view()),
    url(r'^api-localities/(?P<pk>[0-9]+)/$', views.LocalitiesDetail.as_view()),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns = format_suffix_patterns([
    url(r'^api-localities/$',
        views.LocalitiesList.as_view(),
        name='snippet-list'),
    url(r'^api-localities/(?P<pk>[0-9]+)/$',
        views.LocalitiesDetail.as_view(),
        name='snippet-detail'),
])

urlpatterns += [
    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),
    url(r'^$', views.api_root),
]
