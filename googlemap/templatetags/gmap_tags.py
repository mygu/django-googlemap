from django import template
from ..utils import get_location_by_ip


register = template.Library()


@register.inclusion_tag('gmap/mark_location.html', takes_context=True)
def mark_location(context, ip_list, width=None, height=400):
    location_list = [get_location_by_ip(ip) for ip in ip_list]
    context.update({
        'location_list': location_list,
        'width': '%d%s' % (width, 'px') if width else '100%',
        'height': '%d%s' % (height, 'px'),
        'is_resize': 'false'
    })
    return context