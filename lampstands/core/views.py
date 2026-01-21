import requests

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
    
    # Otherwise render the 500.html template
    return render(request, '500.html', status=500)


@api_view(['GET', 'POST'])
def api_root(request, format=None):
    context = {'request': request}
    return Response({
        'localities': reverse('snippet-list', request=request, format=format)
    })


class LocalitiesList(generics.ListCreateAPIView):
    queryset = ChurchPage.objects.all()
    serializer_class = LocalitiesSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class LocalitiesDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ChurchPage.objects.all()
    serializer_class = LocalitiesSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
