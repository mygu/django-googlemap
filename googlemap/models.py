from .settings import MAXMIND_CITY_DB_PATH
from .ip2geo import GeoIP, MEMORY_CACHE

geoip = GeoIP(MAXMIND_CITY_DB_PATH, MEMORY_CACHE)