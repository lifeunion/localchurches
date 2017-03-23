import requests

from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse

from django.template import Context, RequestContext
from django.shortcuts import render_to_response, get_object_or_404

def error404(request):
    if '/play/' in request.path:
        return render(request, 'play_404.html', {'play_404': True},  status=404)
    else:
        return render(request, '404.html', status=404)