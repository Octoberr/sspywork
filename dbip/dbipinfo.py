"""
mmdb
ip信息查询单机版
create by judy 20200428
"""
import argparse
import json
from pathlib import Path

import IPy
import maxminddb


class DBIPINFO(object):

    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("ip", help="ip address, likes 192.168.1.1, 192.168.1.0/24, 192.168.1.0-192.168.1.255")
        self.parser.add_argument("-f", "--inputfile", help="Query the entire file ip address lines dbipinfo")
        self.parser.add_argument("-o", "--outputfile", help="store dpipinfo lines file")
        self.parser.add_argument("--fields", help="show data as the fields likes continent,country,city,isp")
        self.args = self.parser.parse_args()
        if self.args.ip is None and self.args.inputfile is None:
            print('查询ip不能为空，使用-h命令查询需要输入的参数')
            return

    def split_long_ip_ranges(self, ip_ranges):
        """
        如果ip的prefix不是32就需要将每个ip拆分出来
        :return:
        """
        for el in ip_ranges:
            # 这里是处理1.1.0.0/24这个网段的
            if isinstance(el, str):
                try:
                    low_ip = IPy.IP(el)
                    if low_ip.prefixlen() < 32:
                        for ip in low_ip:
                            yield ip.strNormal()
                    else:
                        yield low_ip.strNormal()
                except:
                    # 不是ip段，有可能是域名或者其他东西
                    print(f'Unknown ipstr type ip:{el}')
            elif isinstance(el, tuple):
                st = IPy.IP(el[0])
                sp = IPy.IP(el[1])
                for i in range(st.int(), sp.int() + 1):
                    ipstr: str = IPy.IP(i).strNormal()
                    yield ipstr
            else:
                print(f'Unknown ipstr type ip:{el}')

    def get_ip_geoinfo(self, ip: str) -> dict:
        """
        根据ip去查询所在的地址
        :param ip:
        :return:
        """
        res = None
        try:
            reader = maxminddb.open_database('./_ip_location_dbs/dbfile/geoinfo.mmdb')
            res = reader.get(ip)
            reader.close()
        except Exception as error:
            print("Get geoinfo error:\nip={}\nerror:{}".format(ip, error))
        finally:
            return res

    def parser_ip_addr(self):
        """
        解析ip地址，有这么几种解析方式
        ipstr:
            192.168.1.1, 192.168.1.0/24, 192.168.1.0-192.168.1.255
        ipfile:
            ./ip_ranges.txt
        """
        ipstr = self.args.ip
        ipfile_path = self.args.inputfile
        ip_rangs = []
        if ipstr is not None:
            ip_rangs.extend(ipstr.split(','))
        elif ipfile_path is not None:
            ips_path: Path = Path(ipfile_path)
            ips_info = ips_path.read_text()
            ip_rangs.extend(ips_info.split('\n'))
        else:
            print("There is no ipstr to query dbip")
        for ip in self.split_long_ip_ranges(ip_rangs):
            geoinfo = self.get_ip_geoinfo(ip)
            if geoinfo is not None and isinstance(geoinfo, dict):
                geoinfo['ip'] = ip
                yield geoinfo

    def dis_geoinfo(self, geoinfo: dict, fields: list):
        """
        在命令行展示geoinfo
        """
        ip = geoinfo.get('ip')
        continent = geoinfo.get('continent', {}).get('names', {}).get('zh-CN')
        country = geoinfo.get('country', {}).get('names', {}).get('zh-CN')
        province = geoinfo.get('subdivisions', [])
        pname = None
        if len(province) > 0:
            pd = province[0]
            pname = pd.get('names', {}).get('zh-CN')
        city = geoinfo.get('city', {}).get('names', {}).get('zh-CN')
        lat = geoinfo.get('location', {}).get('latitude')
        lng = geoinfo.get('location', {}).get('longitude')
        isp = geoinfo.get('traits', {}).get('isp')
        org = geoinfo.get('traits', {}).get('organization')
        pstr = f'{ip}    '
        if 'continent' in fields:
            pstr += f'{continent}    '
        if 'country' in fields:
            pstr += f'{country}    '
        if 'province' in fields:
            pstr += f'{pname}    '
        if 'city' in fields:
            pstr += f'{city}    '
        if 'lat' in fields:
            pstr += f'{lat}    '
        if 'lng' in fields:
            pstr += f'{lng}    '
        if 'isp' in fields:
            pstr += f'{isp}    '
        if 'org' in fields:
            pstr += f'{org}    '
        print(pstr.strip())

    def _output_geoinfo(self, geodict, outpath: str):
        """
        输出geo信息
        """
        if outpath is None:
            return
        with open(outpath, 'a', encoding='utf-8') as fp:
            fp.write(json.dumps(geodict, ensure_ascii=False)+'\n')

    def start(self):
        """
        程序入口
        """
        fields = ['ip', 'continent', 'country', 'province', 'city', 'lat', 'lng', 'isp', 'org']
        if self.args.fields is not None:
            fields:list = self.args.fields.split(',')
            if 'ip' not in fields:
                fields.insert(0, 'ip')

        outpath = None
        if self.args.outputfile is not None:
            outpath = self.args.outputfile
        print('    '.join(fields))
        for ginfo in self.parser_ip_addr():
            self._output_geoinfo(ginfo, outpath)
            self.dis_geoinfo(ginfo, fields)
        return


if __name__ == '__main__':
    dbinfo = DBIPINFO()
    dbinfo.start()
