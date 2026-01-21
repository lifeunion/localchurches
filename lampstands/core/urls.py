from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.urlpatterns import format_suffix_patterns
from lampstands.core import views
from .views import LocalitiesList, LocalitiesDetail

urlpatterns = format_suffix_patterns([
    re_path(r'^api-localities/$',
            views.LocalitiesList.as_view(),
            name='snippet-list'),
    re_path(r'^api-localities/(?P<pk>[0-9]+)/$',
            views.LocalitiesDetail.as_view(),
            name='snippet-detail'),
])

urlpatterns += [
    path('api-auth/', include('rest_framework.urls')),
]
