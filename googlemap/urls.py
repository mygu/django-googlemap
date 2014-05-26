from django.conf.urls import patterns, url


urlpatterns = patterns('',
                       url(r'^get_locations/$', 'googlemap.views.get_locations', name='get_locations'),

)
