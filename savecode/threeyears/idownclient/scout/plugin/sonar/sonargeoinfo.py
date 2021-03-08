"""
使用ip去获得ip的归属地
create by judy 20190717
"""

import json
import traceback

import requests
from commonbaby.countrycodes import ALL_COUNTRIES, CountryCode
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.iscoutdataset.iscouttask import IscoutTask
from ....clientdatafeedback.scoutdatafeedback import GeoInfo
from ....config_scouter import scouter_config

logger: MsLogger = MsLogManager.get_logger("Sonarapigeoinfo")


class SonarGeoinfo(object):
    """get geolocation info"""

    @staticmethod
    def get_geoinfo(task: IscoutTask, level: int, ip):
        """
        根据ip去获取地址
        :param ip:
        :return: GeoInfo
        """
        try:
            url = f'{scouter_config.sonarapi}/dbs/iplocations'
            querystring = {"ip": ip}
            headers = {
                'Accept': 'application/json'
            }
            response = requests.request("GET", url, headers=headers, params=querystring, timeout=10)
            res_text = response.text
            res_dict = json.loads(res_text)
            data = res_dict.get('data', [])
            if len(data) == 0:
                return
            ginfo = data[0]

            data_city = ginfo.get('city')
            data_state = ginfo.get('state')
            # country缩写
            data_country = ginfo.get('country')
            data_conuntryfullname = ginfo.get('countryFull')
            lng = ginfo.get('longitude')
            lat = ginfo.get('latitude')
            if not ALL_COUNTRIES.__contains__(data_country) or lat is None or lng is None:
                return
            geoinfo: GeoInfo = GeoInfo(level, lng, lat)

            # 如果能拿到信息那么才去做这么一个事情
            exrtinfo: CountryCode = ALL_COUNTRIES.get(data_country)
            # country
            geoinfo.set_country(data_country, None, None,
                                {'zh-CN': exrtinfo.country_names.get('CN'), 'en': exrtinfo.country_names.get('EN')})
            # subdivisions
            geoinfo.set_province({'zh-CN': None, 'en': data_state})
            # city
            geoinfo.set_city({'zh-CN': None, 'en': data_city})
            geoinfo.globaltelcode = exrtinfo.countrycode
            geoinfo.timezone = exrtinfo.timediffer
            yield geoinfo
        except:
            logger.error(f"Sonarapi get geoinfo error, please check out sonar connect, err:{traceback.format_exc()}")
