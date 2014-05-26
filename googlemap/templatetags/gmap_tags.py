from django import template
from django.utils.safestring import SafeText
from ..utils import get_location_by_ip


register = template.Library()


@register.inclusion_tag('gmap/ip_on_map.html', takes_context=True)
def ip_on_map(context, ip_arg, width=None, height=400, show_input=False):
    if isinstance(ip_arg, list):
        ip_list = ip_arg
    elif isinstance(ip_arg, SafeText):
        ip_list = ip_arg.split(',')
    else:
        ip_list = []
    location_list = [get_location_by_ip(ip) for ip in ip_list]
    context.update({
        'location_list': location_list,
        'width': '%d%s' % (width, 'px') if width else '100%',
        'height': '%d%s' % (height, 'px'),
        'is_resize': 'false',
        'show_input': show_input,
    })
    return context
