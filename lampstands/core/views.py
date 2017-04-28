import requests

from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse, Http404

from django.template import Context, RequestContext
from django.shortcuts import render_to_response, get_object_or_404

from django.http import HttpResponse#, JsonResponse
from .models import ChurchPage
from .serializers import LocalitiesSerializer

from rest_framework import generics
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.decorators import api_view, detail_route
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView

#from rest_framework.views import APIView
#from rest_framework import status, mixins, generics
#from django.views.decorators.csrf import csrf_exempt
#from rest_framework.renderers import JSONRenderer
#from rest_framework.parsers import JSONParser

def error404(request):
    if '/play/' in request.path:
        return render(request, 'play_404.html', {'play_404': True},  status=404)
    else:
        return render(request, '404.html', status=404)

@api_view(['GET'])
@renderer_classes((JSONRenderer,))
def api_root(request, format=None):
    return Response({
        'localities': reverse('localities-list', request=request, format=format)
    })

class LocalitiesList(generics.ListCreateAPIView):
    queryset = ChurchPage.objects.all()
    serializer_class = LocalitiesSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    renderer_classes = (JSONRenderer,)

class LocalitiesDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ChurchPage.objects.all()
    serializer_class = LocalitiesSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    renderer_classes = (JSONRenderer,)

"""
class LocalitiesList(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  generics.GenericAPIView):
    queryset = ChurchPage.objects.all()
    serializer_class = LocalitiesSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

class LocalitiesDetail(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
    queryset = ChurchPage.objects.all()
    serializer_class = LocalitiesSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

class LocalitiesList(APIView):
    def get(self, request, format=None):
        localities = ChurchPage.objects.all()
        serializer = LocalitiesSerializer(localities, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = LocalitiesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LocalitiesDetail(APIView):
    def get_object(self, pk):
        try:
            return ChurchPage.objects.get(pk=pk)
        except ChurchPage.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        locality = self.get_object(pk)
        serializer = LocalitiesSerializer(locality)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        locality = self.get_object(pk)
        serializer = LocalitiesSerializer(locality, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        locality = self.get_object(pk)
        locality.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

#@csrf_exempt
@api_view(['GET', 'POST'])
def localities_list(request, format=None):
    if request.method == 'GET':
        localities = ChurchPage.objects.all()
        serializer = LocalitiesSerializer(localities, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        #data = JSONParser().parse(request)
        serializer = LocalitiesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#@csrf_exempt
@api_view(['GET', 'PUT', 'DELETE'])
def locality_detail(request, pk, format=None):
    try:
        locality = ChurchPage.objects.get(pk=pk)
    except ChurchIndexPage.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = LocalitiesSerializer(locality)
        return Response(serializer.data)

    elif request.method == 'PUT':
        #data = JSONParser().parse(request)
        serializer = LocalitiesSerializer(locality, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        snippet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
"""