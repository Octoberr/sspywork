"""
scouter ip 插件
下载dbip的mmdb数据
mmdb的控制由autotask控制
create by judy 2019/08/28
"""
import datetime
import gzip
import math
import shutil
import threading
import traceback
from pathlib import Path

import maxminddb
import pytz
import requests
from commonbaby.countrycodes import ALL_COUNTRIES, CountryCode
from commonbaby.mslog import MsLogger, MsLogManager

from ..scoutplugbase import ScoutPlugBase
from ....clientdatafeedback.scoutdatafeedback import GeoInfo


class DbipMmdb(ScoutPlugBase):
    # 这个加锁的原因是因为当多个ip scouter需要去下载一个东西的时候不去下载那么多次
    __init_ip_locker = threading.Lock()
    # true if we have downloaded dbip
    _is_dbip_downloaded: bool = False

    def __init__(self):
        ScoutPlugBase.__init__(self)

        # 这个文件夹拿来放压缩包
        # 全放到资源文件夹下去： idown/resource/dbip/
        self.tmppath: Path = Path('./resource/dbip/tmpfile')
        self.tmppath.mkdir(exist_ok=True, parents=True)
        # 这个文件夹拿来放mmdb
        self.dbpath: Path = Path('./resource/dbip/dbfile')
        self.dbpath.mkdir(exist_ok=True, parents=True)

        # 当前db的名字
        self.date_now = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
        self.date = self.date_now.strftime('%Y-%m')
        self.dbname = self.dbpath / f'{self.date}.mmdb'

        self._logger: MsLogger = MsLogManager.get_logger("DBIP-mmdb")

        # 初始化的时候下载dbip库
        self.__init__download_dbip()

    def __init__download_dbip(self):
        """
        多线程检测是否下载了dbip，这样比以前下载的时候去下载dbip要快一点
        modify by judy 2020/03/31
        :return:
        """
        if DbipMmdb._is_dbip_downloaded:
            return
        # 下载数据库的状态
        res = False
        try:
            with DbipMmdb.__init_ip_locker:
                if DbipMmdb._is_dbip_downloaded:
                    return
                # 这里包括检查版本和下载IP库
                res = self.__check_db_version()

        except:
            self._logger.error(f"Init download dbip error, err:{traceback.format_exc()}")
        finally:
            if res:
                # 将下载完成的状态给上
                DbipMmdb._is_dbip_downloaded = True
            else:
                # 将下载完成的状态给上
                DbipMmdb._is_dbip_downloaded = False

    def __download_db(self):
        """
        在dbip网站下载mmdb
        :return:
        """

        res = False
        # date_now = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
        # widgets = [
        #     'Downloading mmdb: ',
        #     progressbar.Bar(),
        #     ' ',
        #     progressbar.Counter(format='%(value)d Mb/%(max_value)d Mb'),
        # ]
        gzname = self.tmppath / f'{self.date}.mmdb.gz'
        dbname = self.dbname
        try:
            # 下载到tmp文件夹
            url = f'https://download.db-ip.com/free/dbip-city-lite-{self.date}.mmdb.gz'
            count = 0
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                total_length = math.ceil(
                    int(r.headers.get('content-length')) / (1024 * 1024))
                with gzname.open('wb') as f:
                    # with progressbar.ProgressBar(max_value=total_length, widgets=widgets) as bar:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        count += 1
                        # bar.update(count)
                        self._logger.info(
                            f'Downloading mmdb: {count} Mb/ {total_length} Mb')
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
            # 解压到db文件夹
            with gzip.open(gzname.as_posix(), 'rb') as f_in:
                with dbname.open('wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            res = True
        except:
            self._logger.info(
                f"Download dbip error, err:{traceback.format_exc()}")
            res = False
        finally:
            # 删除tmppath里面的file
            if gzname.exists():
                gzname.unlink()
        return res

    def __check_db_version(self):
        """
        检测现存的db与当前年月是否对应
        无论如何最后都会在db文件夹存在一个文件
        :return:
        """
        year = self.date_now.year
        month = self.date_now.month
        file_list = [i for i in self.dbpath.iterdir()]
        file_count = len(file_list)
        if file_count == 0:
            return self.__download_db()
        elif file_count > 1:
            # 全部删除了重新下载
            for file in file_list:
                file.unlink()
            return self.__download_db()
        # 现在就只剩下等于1的情况了
        db: Path = file_list[0]
        dbname: str = db.name
        name_list = dbname[:dbname.index('.')].split('-')
        db_year = int(name_list[0])
        db_month = int(name_list[1])
        if db_year == year and db_month == month:
            # 符合要求当月的都能使用
            return True
        else:
            # 已经是新的一月了，那么就删除当月的取下载下月的
            db.unlink()
            return self.__download_db()

    def get_ip_geoinfo(self, level: int, ip: str) -> GeoInfo:
        """
        根据ip去查询所在的地址
        :param level:
        :param ip:
        :return:
        """
        res: GeoInfo = None
        # 检查下初始化是否下载了dbip库，如果没有下载，那么表示网络可能出现了问题
        if not DbipMmdb._is_dbip_downloaded:
            self._logger.error("DBdatabase is not downloaded, check the network")
            return res

        try:
            # 1、先检测下东西在不在
            # 这样当前dbname就一定会有
            # with DbipMmdb.__scouter_ip_locker:
            # 一次只能有一个玩意在这检测版本，虽然慢但是多线程没办法
            # self.__check_db_version()
            reader = maxminddb.open_database(self.dbname.as_posix())
            res = reader.get(ip)
            if res is None:
                return res
            reader.close()

            data_city = res.get('city', {}).get('names', {}).get('en', None)
            data_state = None
            subdivisions = res.get('subdivisions', [])
            if len(subdivisions) == 0:
                data_state = None
            else:
                data_state = subdivisions[0].get('names', {}).get('en', None)
            data_country = res.get('country', {}).get('iso_code', None)
            location = res.get('location', {})
            lng = location.get('longitude', None)
            lat = location.get('latitude', None)
            # 这里表示国家不属于主权国家，所以直接返回None，写注释是一个非常好的习惯
            if not ALL_COUNTRIES.__contains__(
                    data_country) or lat is None or lng is None:
                return res
            geoinfo: GeoInfo = GeoInfo(level, lng, lat)
            exrtinfo: CountryCode = ALL_COUNTRIES.get(data_country)
            geoinfo.set_country(
                data_country, {
                    'zh-CN': exrtinfo.country_names.get('CN'),
                    'en': exrtinfo.country_names.get('EN')
                })
            geoinfo.set_province({'zh-CN': None, 'en': data_state})
            geoinfo.set_city({'zh-CN': None, 'en': data_city})
            geoinfo.globaltelcode = exrtinfo.countrycode
            geoinfo.timezone = exrtinfo.timediffer
            res = geoinfo
        except Exception:
            self._logger.error("Get geoinfo error: ip={}, error: {}".format(
                ip, traceback.format_exc()))
        return res
