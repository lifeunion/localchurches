from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.urlpatterns import format_suffix_patterns
from lampstands.core import views
from django.conf.urls import include
from .views import LocalitiesList, LocalitiesDetail
from wagtail.contrib.wagtailapi import urls as wagtailapi_urls

urlpatterns = [
	url(r'^$', views.api_root),
	url(r'^api-localities/$', views.LocalitiesList.as_view()),
    url(r'^api-localities/(?P<pk>[0-9]+)/$', views.LocalitiesDetail.as_view()),
    url(r'^api/', include(wagtailapi_urls)),
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
]
