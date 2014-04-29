from os.path import join, normpath, dirname, abspath

from django.conf import settings

data_path = normpath(join(dirname(abspath(__file__)), 'data/GeoLiteCity.dat'))

MAXMIND_CITY_DB_PATH = getattr(settings, 'MAXMIND_CITY_DB_PATH', data_path)