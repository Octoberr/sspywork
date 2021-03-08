"""object geolocation info"""

# -*- coding:utf-8 -*-

import threading


class GeoInfo(object):
    """scout object geoinfo"""

    def __init__(
            self,
            # task: IscoutTask,
            level: int,
            longitude,
            latitude,
    ):
        # if not isinstance(task, IscoutTask):
        #     raise Exception("Invalid iscouttask")
        if not isinstance(level, int):
            raise Exception("Invalid level")
        # if not isinstance(longitude, str) or longitude == '':
        #     raise Exception("Invalid domain for whois info")
        if not isinstance(longitude, float):
            raise Exception("Invalid longitude")
        if not isinstance(latitude, float):
            raise Exception("Invalid latitude")

        # self._task: IscoutTask = task # 传进来没用呢先注释了
        self._level: int = level
        self._longitude = longitude
        self._latitude = latitude

        self._continent_code: str = None
        self._continent_geoid: int = None
        self._continent_names: dict = {}
        self._continent_locker = threading.RLock()

        self._country_code: str = None
        self._country_geoid: int = None
        self._country_is_in_eu_union: bool = None
        self._country_names: dict = {}
        self._country_locker = threading.RLock()

        self._province_code: str = None
        self._province_geoid: int = None
        self._province_names: dict = {}
        self._province_locker = threading.RLock()

        self._city_code: str = None
        self._city_geoid: int = None
        self._city_names: dict = {}
        self._city_locker = threading.RLock()

        self.globaltelcode: str = None
        self.timezone: str = None
        # 新增字段
        self.weather_code = None
        # autonomous_system_number
        self.asn = None
        # autonomous_system_organization
        self.aso = None
        # connection_type
        self.ct = None

    def set_continent(self, code: str, geoid: int, names: dict):
        """设置当前geoinfo的大陆,names更新到原有的字典中。有异常抛异常。"""
        if not isinstance(code, str):
            raise Exception("Invalid code for set continent")
        if not isinstance(names, dict) or len(names) < 1:
            raise Exception("Invalid names for set continet")
        with self._country_locker:
            self._continent_code = code
            self._continent_geoid = geoid
            self._continent_names.update(names)

    def set_country(self, code: str, geoid: int, is_in_eu_union: bool, names: dict):
        """设置当前geoinfo的country,names更新到原有的字典中。有异常抛异常。"""
        if not isinstance(code, str):
            raise Exception("Invalid code for set country")
        if not isinstance(names, dict) or len(names) < 1:
            raise Exception("Invalid names for set country")

        with self._country_locker:
            self._country_code = code
            self._country_geoid = geoid
            self._country_is_in_eu_union = is_in_eu_union
            self._country_names.update(names)

    def set_province(self, names: dict, code: str = None, geoid: int = None):
        """设置当前geoinfo的country, names更新到原有的字典中。有异常抛异常。"""
        if not isinstance(names, dict) or len(names) < 1:
            raise Exception("Invalid names for set continet")

        with self._province_locker:
            self._province_code = code
            self._province_geoid = geoid
            self._province_names.update(names)

    def set_city(self, names: dict, code: str = None, geoid: int = None):
        """设置当前geoinfo的country, names更新到原有的字典中。有异常抛异常。"""
        if not isinstance(names, dict) or len(names) < 1:
            raise Exception("Invalid names for set continet")

        with self._city_locker:
            self._city_code = code
            self._city_geoid = geoid
            self._city_names.update(names)

    # def _get_outputdict_sub(self, rootdict: dict):
    #     if not isinstance(rootdict, dict):
    #         raise Exception("Invalid rootdict")

    def get_outputdict(self) -> dict:
        """return geoinfo dict"""
        geodict: dict = {}
        if not geodict.__contains__("location"):
            geodict["location"] = {}
        # location
        geodict["location"]["lat"] = self._latitude
        geodict["location"]["lon"] = self._longitude
        # telcode + timezone
        geodict["globaltelcode"] = self.globaltelcode
        geodict["timezone"] = self.timezone
        if self.weather_code is not None:
            geodict['weather_code'] = self.weather_code
        if self.asn is not None:
            geodict['asn'] = self.asn
        if self.aso is not None:
            geodict['aso'] = self.aso
        if self.ct is not None:
            geodict['connection_type'] = self.ct
        # continent
        if not geodict.__contains__("continent"):
            geodict["continent"] = {}
        if isinstance(self._continent_code, str):
            geodict["continent"]["code"] = self._continent_code
        if self._continent_geoid is not None:
            geodict["continent"]["geoname_id"] = self._continent_geoid
        if len(self._continent_names) > 0:
            geodict["continent"]["names"] = self._continent_names
        # country
        if not geodict.__contains__("country"):
            geodict["country"] = {}
        if isinstance(self._country_code, str):
            geodict["country"]["code"] = self._country_code
        if self._country_geoid is not None:
            geodict["country"]["geoname_id"] = self._country_geoid
        if self._country_is_in_eu_union is not None:
            geodict["country"]["is_in_european_union"] = self._country_is_in_eu_union
        if len(self._country_names) > 0:
            geodict["country"]["names"] = self._country_names
        # province
        if not geodict.__contains__("province"):
            geodict["province"] = {}
        if isinstance(self._province_code, str):
            geodict["province"]["code"] = self._province_code
        if self._province_geoid is not None:
            geodict["province"]["geoname_id"] = self._province_geoid
        if len(self._province_names) > 0:
            geodict["province"]["names"] = self._province_names
        # city
        if not geodict.__contains__("city"):
            geodict["city"] = {}
        if isinstance(self._city_code, str):
            geodict["city"]["code"] = self._city_code
        if self._city_geoid is not None:
            geodict["city"]["geoname_id"] = self._city_geoid
        if len(self._city_names) > 0:
            geodict["city"]["names"] = self._city_names

        return geodict
