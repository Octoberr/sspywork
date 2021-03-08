"""
geoname的爬虫
爬取全球的地理位置信息
create by judy 2019/08/23
"""
import json
import math
import time
import traceback
import zipfile
from pathlib import Path

import requests
from commonbaby.helpers import helper_crypto

from datacontract.automateddataset import EAutoType
from idownclient.clientdatafeedback.autodatafeedback import Geoname
from .country_continent_map import country_map
from ..autopluginbase import AutoPluginBase


class GeoName(AutoPluginBase):
    tasktype = EAutoType.GEONAME

    def __init__(self):
        AutoPluginBase.__init__(self)
        self.admin1_dict = {}
        # 初始化admin1的dict
        self.__get_admin1()

        self.admin2_dict = {}
        self.__get_admin2()

        # 存储下载的zip，并初始化文件夹
        filepath = Path(__file__)
        self.tmpfile = filepath.parent / 'tmpfile'
        self.tmpfile.mkdir(exist_ok=True)

        # 文件后缀名字
        self.suffix = 'geoname'

    def __get_admin1(self):
        """
        获取geonames admin1的字典对应表
        :return:
        """
        url = 'http://download.geonames.org/export/dump/admin1CodesASCII.txt'
        res = requests.get(url, timeout=10)
        res_text = res.text
        lines = res_text.split('\n')
        for line in lines:
            line_info = line.split('\t')
            self.admin1_dict[line_info[-1]] = line_info[0]
        self._logger.info('Get admin1 codes')
        return

    def __get_admin2(self):
        """
        获取geonames admin2的字典对应表
        :return:
        """
        url = 'http://download.geonames.org/export/dump/admin2Codes.txt'
        res = requests.get(url, timeout=10)
        res_text = res.text
        lines = res_text.split('\n')
        for line in lines:
            line_info = line.split('\t')
            self.admin2_dict[line_info[-1]] = line_info[0]
        self._logger.info('Get admin2 codes')
        return

    def __parse_line(self, line: str):
        """
        解析一行数据
        :param line:
        :return:
        """
        try:
            infolist = line.split('\t')
            gid = infolist[0]
            gname = infolist[1]
            geo = Geoname(gid, gname)
            ganame = infolist[2]
            # 替换名字，完整的名字无法去shodan搜索
            alternatenames = infolist[3].split(',')
            # 给asciiname fuzhi
            for atname in alternatenames:
                if len(atname.split(' ')) == 1:
                    geo.asciiname = ganame
                    break
            if geo.asciiname is None and ganame != '':
                geo.asciiname = ganame

            glat = infolist[4]
            if glat != '':
                geo.latitude = glat

            glng = infolist[5]
            if glng != '':
                geo.longitude = glng

            featureclass = infolist[6]
            if featureclass != '':
                geo.feature_class = featureclass

            featurecode = infolist[7]
            if featurecode != '':
                geo.featurecode = featurecode

            population = infolist[14]
            if population != '':
                geo.population = population

            timezone = infolist[17]
            if timezone != '':
                geo.timezone = timezone

            modification = infolist[18]
            if modification != '':
                geo.modification = modification

            # -----------------------------------下面是比较复杂的了
            country_code = infolist[8]
            continent = country_map.get(country_code, None)
            geo.continent = continent
            # parent_admin_code
            pac = {}
            pac['countrycode'] = country_code
            pac['admin1code'] = infolist[10]
            pac['admin2code'] = infolist[11]
            pac['admin3code'] = infolist[12]
            pac['admin4code'] = infolist[13]
            geo.set_parent_admin_code(pac)
            # self_admin_code
            sac = {}
            sac['countrycode'] = country_code
            # 目前只有一级行政区和二级行政区有自己的admin_code
            # 一级行政区
            if featurecode == 'ADM1':
                sac_str = self.admin1_dict.get(gid)
                if sac_str is not None:
                    sac_list = sac_str.split('.')
                    sac['admin1code'] = sac_list[-1]
                geo.set_self_admin_code(sac)
            # 二级行政区
            if featurecode == 'ADM2':
                sac_str = self.admin2_dict.get(gid)
                if sac_str is not None:
                    sac_list = sac_str.split('.')
                    sac['admin1code'] = sac_list[-2]
                    sac['admin2code'] = sac_list[-1]
                geo.set_self_admin_code(sac)
        except Exception as ex:
            self._logger.error(f'Parse line error, err:{ex}')
            geo = None
        return geo

    def __get_geoname(self, datapath: Path):
        """
        获取解压后的文件路径，读取大文件中的数据并输出
        :param datapath:
        :return:
        """
        with datapath.open('r', encoding='utf-8') as infile:
            for line in infile:
                try:
                    geo = self.__parse_line(line)
                    if geo is not None:
                        yield geo
                except:
                    self._logger.error(f'Parse line error, err:{traceback.format_exc()}')
                    continue

    def get_all_country(self):
        """
        下载所有城市的zip，解压并解析
        :return:
        """
        # 下载
        # widgets = [
        #     'Downloading allCountries.zip: ',
        #     progressbar.Bar(),
        #     ' ',
        #     progressbar.Counter(format='%(value)d Mb/%(max_value)d Mb'),
        # ]

        filename = self.tmpfile / 'allinfo.zip'
        url = 'http://download.geonames.org/export/dump/allCountries.zip'
        headers = {
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            'Accept-Encoding': "gzip, deflate",
            'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
            'Cache-Control': "no-cache",
            'Connection': "keep-alive",
            'Host': "download.geonames.org",
            'Pragma': "no-cache",
            'Referer': "http://download.geonames.org/export/dump/",
            'Upgrade-Insecure-Requests': "1",
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36"
        }
        count = 0
        with requests.get(url, headers=headers, stream=True) as r:
            r.raise_for_status()
            total_length = math.ceil(int(r.headers.get('content-length')) / (1024 * 1024))
            with filename.open('wb') as f:
                # with progressbar.ProgressBar(max_value=total_length, widgets=widgets) as bar:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    count += 1
                    # bar.update(count)
                    self._logger.info(f'Downloading allCountries.zip: {count} Mb/ {total_length} Mb')
                    # self._logger.info(f'{count} times Downloaded 1Mb, and waiting...')
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
        self._logger.info('Download all city info zip success')
        # 解压
        self._logger.debug('Start unzip')
        zip_file = zipfile.ZipFile(filename, 'r')
        zip_file.extractall(self.tmpfile)
        zipinfo = zip_file.namelist()
        self._logger.debug(f'Get unzip file, name:{zipinfo[0]}')
        zip_file.close()
        # 并解析
        info_path = self.tmpfile / zipinfo[0]
        for g_data in self.__get_geoname(info_path):
            geo_dict = g_data.__dict__
            # 增量下载
            geostr = json.dumps(geo_dict, ensure_ascii=False)
            geo_md5 = helper_crypto.get_md5_from_str(geostr)
            # 判断数据是否重复，如果重复那么就不不输出数据，这样是用客户端分担了server的运算量
            if self.is_geodata_unique(geo_md5):
                continue
            # 数据不重复表示新数据，输出数据，保存数据的唯一标识
            self.write_text(geostr, self.suffix)
            self.store_geodata_unique(geo_md5)

        # 下载完成数据后删除文件，
        # 因为这个文件好像每个月都在更新，
        # 所以拿到数据后就去从新下载比较好
        # 最后清理下载的数据
        time.sleep(5)
        info_path.unlink()
        filename.unlink()
        self._logger.debug('Delete source zip file')

    def start(self):
        with self.file_locker:
            self.get_all_country()
