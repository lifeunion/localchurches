from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static

from lampstands.core import views

urlpatterns = [
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)