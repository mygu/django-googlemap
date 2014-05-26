import json

from django.http import HttpResponse
from .models import geoip


def get_location_by_ip(ip):
    """
    Returns longitude(lng) and latitude(lat) according use ip address by the geo
    """
    try:
        location = geoip.ipaddress_to_location(ip)
    except Exception as e:
        location = None
    return location


def json_result(request, data):
    response_data = json.dumps(data)
    if 'application/json' in request.META.get('HTTP_ACCEPT_ENCODING', None):
        mimetype = 'application/json'
    else:
        mimetype = 'text/plain'
    return HttpResponse(response_data, mimetype=mimetype)