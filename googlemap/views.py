from .utils import get_location_by_ip, json_result


def get_locations(request):
    location_list = []
    try:
        ip_string = request.REQUEST.get('ip_string', None)
        if ip_string:
            ip_list = ip_string.split(',')
            location_list = [get_location_by_ip(ip) for ip in ip_list]
        result = {'status': 'success', 'data': location_list}
        return json_result(request, result)
    except Exception as e:
        result = {'status': 'error', 'data': e.message}