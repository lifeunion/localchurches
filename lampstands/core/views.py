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
