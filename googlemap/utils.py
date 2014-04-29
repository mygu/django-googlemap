from .models import geoip


def get_location_by_ip(ip):
    """
    Returns longitude(lng) and latitude(lat) according use ip address by the geo
    """
    try:
        location = geoip.ipaddress_to_location(ip)
    except Exception as e:
        location = {
            'lng': 0,
            'lat': 0
        }
    return location