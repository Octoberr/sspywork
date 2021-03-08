"""
scouter ip 插件
下载dbip的mmdb数据
mmdb的控制由autotask控制
create by judy 2019/08/28

更新dbip的离线数据库，统一使用geoloc
create by judy 2020/04/24
"""
import traceback

from datacontract import EClientBusiness
from ....config_client import basic_client_config
clientbusiness = eval(basic_client_config.clientbusiness)
if EClientBusiness.ALL.value in clientbusiness or EClientBusiness.IScoutTask.value in clientbusiness:
    from geoiploc.geoiploc import GeoIPLoc

from commonbaby.countrycodes import ALL_COUNTRIES, CountryCode
from commonbaby.mslog import MsLogger, MsLogManager

from ..scoutplugbase import ScoutPlugBase
from ....clientdatafeedback.scoutdatafeedback import GeoInfo


class DbipMmdb(ScoutPlugBase):

    def __init__(self):
        ScoutPlugBase.__init__(self)

        self._logger: MsLogger = MsLogManager.get_logger("DBIP-mmdb")

    def format_string(self, instr):
        """
        有些国家的中文出现了带有分号的情况，
        这里统一处理下
        20200927 目前只有国家出现了这个数据
        """
        try:
            res = None
            if instr is None or instr == '':
                return
            res_strip: str = instr.strip()
            if res_strip.endswith(';'):
                res = res_strip[:res_strip.index(';')]
            else:
                res = res_strip
        except:
            self._logger.error(f"Format dbipinfo {instr} error, err:{traceback.format_exc()}")
        return res

    def get_ip_mmdbinfo(self, level: int, ip: str):
        """
        根据ip去查询所在的地址
        :param level:
        :param ip:
        :return:
        """
        res: GeoInfo = None
        org = None
        isp = None
        try:
            res_dict = GeoIPLoc.get_ip_location(ip)
            # 新镇获取isp和org信息
            traits_info = res_dict.get('traits', {})
            org = traits_info.get('organization', None)
            isp = traits_info.get('isp', None)
            # autonomous_system_number
            asn = traits_info.get('autonomous_system_number', None)
            # autonomous_system_organization
            aso = traits_info.get('autonomous_system_organization', None)
            # connection_type
            ct = traits_info.get('connection_type', None)

            # cityinfo
            data_city_info = res_dict.get('city', {})
            data_city_geoid = data_city_info.get('geoname_id', None)
            data_city_en = data_city_info.get('names', {}).get('en', None)
            data_city_cn = data_city_info.get('names', {}).get('zh-CN', None)
            # provinceinfo
            data_state_en = None
            data_state_cn = None
            data_state_geoid = None
            data_state_isocode = None
            subdivisions = res_dict.get('subdivisions', [])
            if len(subdivisions) > 0:
                data_state_info = subdivisions[0]
                data_state_geoid = data_state_info.get('geoname_id', None)
                data_state_isocode = data_state_info.get('iso_code', None)
                data_state_en = data_state_info.get('names', {}).get('en', None)
                data_state_cn = data_state_info.get('names', {}).get('zh-CN', None)
            # countryinfo
            data_country_info = res_dict.get('country', {})
            data_country_geoid = data_country_info.get('geoname_id', None)
            data_country_code = data_country_info.get('iso_code', None)
            data_country_is_in_eu_union = data_country_info.get('is_in_european_union', False)
            data_country_en = data_country_info.get('names', {}).get('en')
            data_country_cn = self.format_string(data_country_info.get('names', {}).get('zh-CN'))
            # location info
            location = res_dict.get('location', {})
            lng = location.get('longitude', None)
            lat = location.get('latitude', None)
            # time_zone = location.get('time_zone', None)
            weather_code = location.get('weather_code', None)
            # 这里表示国家不属于主权国家，所以直接返回None，写注释是一个非常好的习惯
            if not ALL_COUNTRIES.__contains__(data_country_code) or lat is None or lng is None:
                return res, org, isp
            geoinfo: GeoInfo = GeoInfo(level, lng, lat)
            geoinfo.set_country(
                data_country_code, data_country_geoid, data_country_is_in_eu_union,
                {
                    'zh-CN': data_country_cn,
                    'en': data_country_en
                })
            geoinfo.set_province({'zh-CN': data_state_cn, 'en': data_state_en}, code=data_state_isocode,
                                 geoid=data_state_geoid)
            geoinfo.set_city({'zh-CN': data_city_cn, 'en': data_city_en}, geoid=data_city_geoid)
            # 大洲
            ctinfo = res_dict.get('continent', {})
            ctcode = ctinfo.get('code')
            ctgeoid = ctinfo.get('geoname_id')
            ctname_en = ctinfo.get('names', {}).get('en')
            ctname_cn = ctinfo.get('names', {}).get('zh-CN')
            geoinfo.set_continent(ctcode, ctgeoid, {'zh-CN': ctname_cn, 'en': ctname_en})
            exrtinfo: CountryCode = ALL_COUNTRIES.get(data_country_code)
            geoinfo.globaltelcode = exrtinfo.countrycode
            geoinfo.timezone = exrtinfo.timediffer
            # 新增字段
            geoinfo.weather_code = weather_code
            geoinfo.asn = asn
            geoinfo.aso = aso
            geoinfo.ct = ct
            res = geoinfo
        except Exception:
            self._logger.error("Get geoinfo error: ip={}, error: {}".format(
                ip, traceback.format_exc()))
        return res, org, isp
