import math
import mmap
import gzip

import pytz

import os
import codecs
import const
from util import ip2long
from googlemap.ip2geo.timezone import time_zone_by_country_and_region


MMAP_CACHE = const.MMAP_CACHE
MEMORY_CACHE = const.MEMORY_CACHE
STANDARD = const.STANDARD


class GeoIPError(Exception):
    pass


class GeoIPMetaclass(type):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instances'):
            cls._instances = {}

        if len(args) > 0:
            filename = args[0]
        elif 'filename' in kwargs:
            filename = kwargs['filename']

        if not filename in cls._instances:
            cls._instances[filename] = type.__new__(cls, *args, **kwargs)

        return cls._instances[filename]


GeoIPBase = GeoIPMetaclass('GeoIPBase', (object,), {})


class GeoIP(GeoIPBase):
    def __init__(self, filename, flags=0):
        """
        Initialize the class.

        @param filename: path to a geoip database. If MEMORY_CACHE is used,
            the file can be gzipped.
        @type filename: str
        @param flags: flags that affect how the database is processed.
            Currently the only supported flags are STANDARD (the default),
            MEMORY_CACHE (preload the whole file into memory), and
            MMAP_CACHE (access the file via mmap).
        @type flags: int
        """
        self._filename = filename
        self._flags = flags

        if self._flags & const.MMAP_CACHE:
            with open(filename, 'rb') as f:
                self._filehandle = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        elif self._flags & const.MEMORY_CACHE:
            try:
                self._filehandle = gzip.open(filename, 'rb')
                self._memoryBuffer = self._filehandle.read()
            except IOError:
                self._filehandle = codecs.open(filename, 'rb', 'latin_1')
                self._memoryBuffer = self._filehandle.read()

        else:
            self._filehandle = codecs.open(filename, 'rb', 'latin_1')

        self._setup_segments()

    def _setup_segments(self):
        """
        Parses the database file to determine what kind of database is being used and setup
        segment sizes and start points that will be used by the seek*() methods later.
        """
        self._databaseType = const.CITY_EDITION_REV1
        self._recordLength = const.STANDARD_RECORD_LENGTH

        filepos = self._filehandle.tell()
        self._filehandle.seek(-3, os.SEEK_END)

        for i in range(const.STRUCTURE_INFO_MAX_SIZE):
            delim = self._filehandle.read(3)

            if delim == unichr(255) * 3:
                self._databaseType = ord(self._filehandle.read(1))

                if self._databaseType in (const.CITY_EDITION_REV0,
                                          const.CITY_EDITION_REV1):
                    self._databaseSegments = 0
                    buf = self._filehandle.read(const.SEGMENT_RECORD_LENGTH)

                    for j in range(const.SEGMENT_RECORD_LENGTH):
                        self._databaseSegments += (ord(buf[j]) << (j * 8))

                break
            else:
                self._filehandle.seek(-4, os.SEEK_CUR)

        self._filehandle.seek(filepos, os.SEEK_SET)

    def _seek_country(self, ipnum):
        """
        Using the record length and appropriate start points, seek to the
        country that corresponds to the converted IP address integer.

        @param ipnum: result of ip2long conversion
        @type ipnum: int
        @return: offset of start of record
        @rtype: int
        """
        offset = 0

        for depth in range(31, -1, -1):

            if self._flags & const.MEMORY_CACHE:
                startIndex = 2 * self._recordLength * offset
                length = 2 * self._recordLength
                endIndex = startIndex + length
                buf = self._memoryBuffer[startIndex:endIndex]
            else:
                self._filehandle.seek(2 * self._recordLength * offset, os.SEEK_SET)
                buf = self._filehandle.read(2 * self._recordLength)

            x = [0, 0]

            for i in range(2):
                for j in range(self._recordLength):
                    x[i] += ord(buf[self._recordLength * i + j]) << (j * 8)

            if ipnum & (1 << depth):

                if x[1] >= self._databaseSegments:
                    return x[1]

                offset = x[1]

            else:

                if x[0] >= self._databaseSegments:
                    return x[0]

                offset = x[0]

        raise Exception('Error traversing database - perhaps it is corrupt?')

    def _get_record(self, ipnum):
        """
        Populate location dict for converted IP.

        @param ipnum: converted IP address
        @type ipnum: int
        @return: dict with country_code, country_code3, country_name,
            region, city, postal_code, latitude, longitude,
            dma_code, metro_code, area_code, region_name, time_zone
        @rtype: dict
        """
        seek_country = self._seek_country(ipnum)
        if seek_country == self._databaseSegments:
            return None

        record_pointer = seek_country + (2 * self._recordLength - 1) * self._databaseSegments

        self._filehandle.seek(record_pointer, os.SEEK_SET)
        record_buf = self._filehandle.read(const.FULL_RECORD_LENGTH)

        record = {}

        record_buf_pos = 0
        char = ord(record_buf[record_buf_pos])
        record['country_code'] = const.COUNTRY_CODES[char]
        record['country_code3'] = const.COUNTRY_CODES3[char]
        record['country_name'] = const.COUNTRY_NAMES[char]
        record_buf_pos += 1
        str_length = 0

        # get region
        char = ord(record_buf[record_buf_pos + str_length])
        while (char != 0):
            str_length += 1
            char = ord(record_buf[record_buf_pos + str_length])

        if str_length > 0:
            record['region_name'] = record_buf[record_buf_pos:record_buf_pos + str_length]

        record_buf_pos += str_length + 1
        str_length = 0

        # get city
        char = ord(record_buf[record_buf_pos + str_length])
        while (char != 0):
            str_length += 1
            char = ord(record_buf[record_buf_pos + str_length])

        if str_length > 0:
            record['city'] = record_buf[record_buf_pos:record_buf_pos + str_length]
        else:
            record['city'] = ''

        record_buf_pos += str_length + 1
        str_length = 0

        # get the postal code
        char = ord(record_buf[record_buf_pos + str_length])
        while (char != 0):
            str_length += 1
            char = ord(record_buf[record_buf_pos + str_length])

        if str_length > 0:
            record['postal_code'] = record_buf[record_buf_pos:record_buf_pos + str_length]
        else:
            record['postal_code'] = None

        record_buf_pos += str_length + 1
        str_length = 0

        latitude = 0
        longitude = 0
        for j in range(3):
            char = ord(record_buf[record_buf_pos])
            record_buf_pos += 1
            latitude += (char << (j * 8))

        record['latitude'] = (latitude / 10000.0) - 180.0

        for j in range(3):
            char = ord(record_buf[record_buf_pos])
            record_buf_pos += 1
            longitude += (char << (j * 8))

        record['longitude'] = (longitude / 10000.0) - 180.0

        if self._databaseType == const.CITY_EDITION_REV1:
            dmaarea_combo = 0
            if record['country_code'] == 'US':
                for j in range(3):
                    char = ord(record_buf[record_buf_pos])
                    record_buf_pos += 1
                    dmaarea_combo += (char << (j * 8))

                record['dma_code'] = int(math.floor(dmaarea_combo / 1000))
                record['area_code'] = dmaarea_combo % 1000
        else:
            record['dma_code'] = 0
            record['area_code'] = 0

        if 'dma_code' in record and record['dma_code'] in const.DMA_MAP:
            record['metro_code'] = const.DMA_MAP[record['dma_code']]
        else:
            record['metro_code'] = ''

        if 'country_code' in record:
            record['time_zone'] = time_zone_by_country_and_region(
                record['country_code'], record.get('region_name')) or ''
        else:
            record['time_zone'] = ''

        return record

    def ipaddress_to_timezone(self, ipaddress):
        """
        Look up the time zone for a given IP address.
        Use this method if you have a Region or City database.

        @param hostname: IP address
        @type hostname: str
        @return: A datetime.tzinfo implementation for the given timezone
        @rtype: datetime.tzinfo
        """
        try:
            ipnum = ip2long(ipaddress)

            if not ipnum:
                raise ValueError("Invalid IP address: %s" % ipaddress)

            if not self._databaseType in (const.CITY_EDITION_REV0, const.CITY_EDITION_REV1):
                raise GeoIPError('Invalid database type; region_* methods expect ' \
                                 'Region or City database')

            tz_name = self._get_record(ipnum)['time_zone']
            if tz_name:
                tz = pytz.timezone(tz_name)
            else:
                tz = None
            return tz

        except ValueError:
            raise GeoIPError(
                '*_by_addr methods only accept IP addresses. Use *_by_name for hostnames. (Address: %s)' % ipaddress)


    def ipaddress_to_location(self, ipaddress):
        """
        Look up the time zone for a given IP address.
        Use this method if you have a Region or City database.

        @param hostname: IP address
        @type hostname: str
        @return: location of lng and lat
        @rtype: string
        """
        try:
            ipnum = ip2long(ipaddress)

            if not ipnum:
                raise ValueError("Invalid IP address: %s" % ipaddress)

            if not self._databaseType in (const.CITY_EDITION_REV0, const.CITY_EDITION_REV1):
                raise GeoIPError('Invalid database type; region_* methods expect ' \
                                 'Region or City database')

            lng = self._get_record(ipnum)['longitude']
            lat = self._get_record(ipnum)['latitude']

            return {
                'lng': lng,
                'lat': lat
            }

        except ValueError:
            raise GeoIPError(
                '*_by_addr methods only accept IP addresses. Use *_by_name for hostnames. (Address: %s)' % ipaddress)