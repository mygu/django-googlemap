================
django-googlemap
================

django-googlemap is a simple Django app to show the google map from ip addresses.

Detailed documentation is in the "docs" directory.

Quick start
-----------

1. Install django-googlemap::

    pip install django-googlemap

2. Add "django-googlemap" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = (
        ...
        'googlemap',
    )

3. In your template html::

    {% load gmap_tags %}
    
    <!--
        <ip_list> is a list of ip addresses
        <width> default is auto
        <height> default is 400px
      -->
    {% ip_on_map <ip_List> <width> <height> %}

4. Settings(optional)::

    # Download maxmind free geo database from http://dev.maxmind.com/geoip/legacy/geolite/

    MAXMIND_CITY_DB_PATH = 'Your data file path'

