import csv
import json
from pathlib import Path
from rdap.ipwhois import IPWhois

import maxminddb

import queue
import threading


class Analysisdata(object):

    def __init__(self):
        self._path = Path('./_outputpath')
        self.whois = IPWhois()
        self.q = queue.Queue()
        self.qwrite = queue.Queue()

        self.cnt = 0

    def _write_csv_header(self):
        """
        编写csv文件的头部
        :return:
        """
        csvfile = open(f'./analysisipm.csv', 'a', newline='')
        fieldnames = ['ip', 'lat', 'lng', 'countryname', 'countrycode', 'province', 'city', 'org', 'isp', '生效时间',
                      '失效时间', '相关实体信息']

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        csvfile.close()
        return

    def get_ip_geoinfo(self, ip: str) -> dict:
        """
        根据ip去查询所在的地址
        :param ip:
        :return:
        """
        res = {}
        try:
            # 1、先检测下东西在不在
            # 这样当前dbname就一定会有
            # with DbipMmdb.__scouter_ip_locker:
            # 一次只能有一个玩意在这检测版本，虽然慢但是多线程没办法
            # self.__check_db_version()
            reader = maxminddb.open_database('./_ip_location_dbs/dbfile/2020-04.mmdb')
            res = reader.get(ip)
            if res is None:
                return res
            reader.close()

            # data_city = res.get('city', {}).get('names', {}).get('en', None)
            # data_state = None
            # subdivisions = res.get('subdivisions', [])
            # if len(subdivisions) == 0:
            #     data_state = None
            # else:
            #     data_state = subdivisions[0].get('names', {}).get('en', None)
            # data_country = res.get('country', {}).get('iso_code', None)
            # location = res.get('location', {})
            # lng = location.get('longitude', None)
            # lat = location.get('latitude', None)
            # 这里表示国家不属于主权国家，所以直接返回None，写注释是一个非常好的习惯
            # if not ALL_COUNTRIES.__contains__(
            #         data_country) or lat is None or lng is None:
            #     return res
            # geoinfo: GeoInfo = GeoInfo(level, lng, lat)
            # exrtinfo: CountryCode = ALL_COUNTRIES.get(data_country)
            # geoinfo.set_country(
            #     data_country, {
            #         'zh-CN': exrtinfo.country_names.get('CN'),
            #         'en': exrtinfo.country_names.get('EN')
            #     })
            # geoinfo.set_province({'zh-CN': None, 'en': data_state})
            # geoinfo.set_city({'zh-CN': None, 'en': data_city})
            # geoinfo.globaltelcode = exrtinfo.countrycode
            # geoinfo.timezone = exrtinfo.timediffer
            # res = geoinfo
        except Exception as error:
            print("Get geoinfo error:\nip={}\nerror:{}".format(ip, error))
        finally:
            return res

    def get_ip_whois(self, ip):
        """

        :param ip:
        :return:
        """
        # res = self.whois.get_ipwhois(ip, 'asd')

        for res in self.whois.get_ipwhois_history(ip, 'no', 1):
            if res is not None:
                yield res.get_outputdict()
        # return {}

    # if res is None:
    #     return {}
    # return res.get_outputdict()

    def process_data(self):
        cnt = 0
        for file in self._path.iterdir():
            self.q.put(file)
            self.cnt += 1
            print("put {}".format(self.cnt))

    def getinfo(self):
        while True:
            try:
                file = self.q.get()

                write_line = {}
                res = file.read_text(encoding='utf-8')
                res_dict = json.loads(res)
                ip = res_dict.get('ip')
                write_line['ip'] = ip
                new_res = self.get_ip_geoinfo(ip)

                write_line['lat'] = new_res.get('location').get('latitude')
                write_line['lng'] = new_res.get('location').get('longitude')
                write_line['countryname'] = new_res.get('country').get('names').get('zh-CN')
                write_line['countrycode'] = new_res.get('country').get('iso_code')
                province = new_res.get('subdivisions', [])
                if len(province) > 0:
                    write_line['province'] = province[0].get('names').get('zh-CN')
                write_line['city'] = new_res.get('city').get('names').get('zh-CN')
                write_line['org'] = new_res.get('traits').get('organization')
                write_line['isp'] = new_res.get('traits').get('isp')
                stime = ''
                etime = ''
                entities = []
                for whoisdata in self.get_ip_whois(ip):
                    stime = whoisdata.get('applicable_from', '')
                    etime = whoisdata.get('last_modified', '')
                    entities.append(whoisdata.get('entities', ''))

                write_line['生效时间'] = stime
                write_line['失效时间'] = etime
                # entites = whoisdata.get('entities')
                # if len(entites) > 0:

                write_line['相关实体信息'] = json.dumps(entities)

                self.qwrite.put(write_line)
            except Exception as e:
                print(e)

    def writecsv(self):
        self._write_csv_header()
        csvfile = open(f'./analysisipm.csv', 'a', newline='')
        fieldnames = ['ip', 'lat', 'lng', 'countryname', 'countrycode', 'province', 'city', 'org', 'isp', '生效时间',
                      '失效时间', '相关实体信息']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        currcnt = 0
        while True:
            try:
                write_line = self.qwrite.get()
                writer.writerow(write_line)
                currcnt += 1
                print("write {}".format(currcnt))
                if currcnt >= self.cnt:
                    break
            except Exception as e:
                print(e)
        csvfile.close()
        print('done')


if __name__ == '__main__':
    aa = Analysisdata()
    aa.process_data()

    for i in range(30):
        t = threading.Thread(target=aa.getinfo)
        t.start()

    tt = threading.Thread(target=aa.writecsv)
    tt.start()
    tt.join()
