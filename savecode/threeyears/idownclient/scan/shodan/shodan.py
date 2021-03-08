"""
iscan shodan 插件
create by judy 2019/07/25
"""
import json
import time
import traceback
from uuid import uuid1
import pytz

import requests
from datetime import datetime

from pathlib import Path
from commonbaby.helpers import helper_str
from datacontract import IscanTask, ECommandStatus
from idownclient.clientdatafeedback.scandatafeedback import Search
from .shodanbase import ShodanBase
import shodan
import uuid


class Shodan(ShodanBase):
    def __init__(self, task: IscanTask):
        ShodanBase.__init__(self, task)
        # 项目内部使用，用于判断数据是否已经全部获取完成
        self.__get_data_complete = False

        # 用于去重使用
        self.__remove_duplicate_dict = {}

    def __judge_port_service(self, http, ssl, ftp, ssh, opts: dict):
        """
        根据端口开放的服务来给出该端口的应用层协议
        :param http:
        :param ssl:
        :param ftp:
        :param ssh:
        :param opts:
        :return:
        """
        service = None
        if http is not None and ssl is None:
            service = 'http'
            return service
        if http is not None and ssl is not None:
            service = 'https'
            return service
        if ftp is not None:
            service = 'ftp'
            return service
        if ssh is not None:
            service = 'ssh'
            return service
        if opts.get('telnet') is not None:
            service = 'telnet'
            return service
        # 最后如果没有找到服务那么就是unknown
        if service is None:
            return 'unknown'

    def __remove_duplicate_data(self, page: int, ipstr):
        """
        相邻页数去重，字典里只保留3页的数据，同时与前两页的数据进行比较
        重复为 true
        不重复为false
        这里逻辑已经更改，现在已经允许跳过某页
        TMD这个去重根本没有生效
        1、还是只对相邻的页数去重，如果相邻的不存在那么就直接删除了
        这个去重不能这么写，有问题的说
        """
        dupres = False
        try:
            # 1、先保存数据，判断有没有创建当前页的列表，没有的话创建，有的话直接添加
            pagelist = self.__remove_duplicate_dict.get(page, [])
            pagelist.append(ipstr)
            # 2、去前两页找相关的
            # 先-1
            page -= 1
            flist = self.__remove_duplicate_dict.get(page)
            if flist is not None:
                if ipstr in flist:
                    dupres = True
                    # return dupres
            # page 再-1
            page -= 1
            fflist = self.__remove_duplicate_dict.get(page)
            if fflist is not None:
                if ipstr in fflist:
                    dupres = True
                    # return dupres
        except:
            self._logger.error(
                f"Remove duplicate_data error, err:{traceback.format_exc()}")
        finally:
            # page 再-1，只保存3页删除前3页的
            page -= 1
            self.__remove_duplicate_dict.pop(page, None)
        return dupres

    def _parse_dict(self, dinfo: dict, page, ips: dict = None):
        """
        解析一个数据，shodan的数据有点详细
        每条数据中就只会有一个ip和一个port
        :param dinfo:
        :param page:
        :param ips:
        :return:
        """
        sinfo = None
        try:
            # 常用或者是复用字段
            # ip会拿去单独查询
            # 过滤数据数据格式为 ip:port
            # rport = dinfo.get('port')
            # 去重需要，后期换了redis或者其他策略再去重吧
            # undata = f'{ip}:{rport}'

            # r_res = self.__remove_duplicate_data(page, undata)
            # if r_res:
            #     return sinfo
            ip = dinfo.get('ip_str')
            # 只有搜索才需要保存ip信息
            if ips is not None:
                ips[ip] = 1

            domains: list = dinfo.get('domains', [])
            org = dinfo.get('org')
            isp = dinfo.get('isp')
            hostnames: list = dinfo.get('hostnames', [])
            vulns = dinfo.get('vulns', None)
            # portinfo--------------------------------------------
            pinf = self._parse_portinfo(dinfo, hostnames, domains, ip, vulns)
            # geo---------------------------------------------
            asn = dinfo.get('asn')
            location: dict = dinfo.get('location')
            gin = self._parse_geoinfo(asn, location)
            # --------------------------------------------
            # 收集到的与domain相关的所有东西
            hostnames.extend(domains)
            # --------------------------------------------------------
            sinfo = Search(self.task, ip, hostnames, vulns, gin, pinf)
            sinfo.org = org
            sinfo.isp = isp
        except:
            self._logger.error(
                f'Get shodan data error, err:{traceback.format_exc()}')
        return sinfo

    def __wait_time(self, ws: int):
        """
        打印等待时间
        :param ws:
        :return:
        """
        for i in range(ws // 10):
            self._logger.info(f'Has been waiting for {(i + 1) * 10} seconds')
            time.sleep(10)

    def _get_shodan_resultjson(self, url):
        """
        这里是去拿shodan server上的数据，可能会出的错有两种
        1、本身的网络错误，这种尝试一下就行
        2、shodan服务器爆出的错，这种也需要不断尝试
        但是这个方法就只去管网络出的错
        但是这个结构直接优化为返回拿取数据，职能变简单，逻辑变清晰
        :param url:
        :return:
        """
        html = None
        while True:
            try:
                response = requests.get(url, timeout=60)
                if response.status_code != 200:
                    raise Exception(
                        f'Request canot connet to url, status code:{response.status_code}'
                    )
                html = response.text
                self.errortimes = 0
                return html
            except Exception as ex:
                self.errortimes += 1
                self._logger.error(
                    f'Shodan server raise error\nError times:{self.errortimes}'
                )
                self._logger.error(
                    f'Search task will retry in a minute\nurl:{url}\nreason:{ex}'
                )
                # 连续报错次数大于设置的报错限制，那么就直接退出了
                if self.errortimes > self.error_limit:
                    return html
                self.__wait_time(60)
                continue

    def _download_ip_info(self, ips):
        """
        下载一个ip的所有信息
        这里是用于搜索后的ip再去下载详细信息
        这样优化一下逻辑瞬间就清晰了
        虽然写了重复的代码，但是每个下载查询的职能不同，重复使得逻辑更为清晰
        :return:
        """
        page_start = 1
        all_ipcount = len(ips)
        i = 0
        for ip in ips.keys():
            # ip = ip_list[i]
            try:
                querys = f'ip:{ip}'
                url = f'{self._basic_url}/shodan/host/search?key={self.apikey}&query={querys}&page={page_start}'
                self._logger.debug(f'Query url:{url}')
                html = self._get_shodan_resultjson(url)
                if html is None:
                    continue
                s_dict: dict = json.loads(html, encoding='utf-8')
                # s_dict: dict = self.json_loads_byteified(html)
                # s_dict: dict = helper_str.parse_js(html)
                matches = s_dict.get('matches', [])
                for match in matches:
                    res = self._parse_dict(match, page_start, ips)
                    if res is not None:
                        yield res.__dict__
            except:
                self._logger.error(
                    f'Get ip info error,err:{traceback.format_exc()}')
                continue
            finally:
                time.sleep(1)
                i += 1
                progress = round((i * 100 / all_ipcount), 2)
                if progress > 100: progress = 100
                self.task.progress = progress
                self._write_iscantaskback(ECommandStatus.Dealing,
                                          f'下载ip详细信息，进度:{progress}%')

        self._logger.info('Complete download ip info')

    def _download_search_data(self) -> iter:
        """
        实现下载搜索数据，不需要保存下载到哪里了，下载数据量比较小
        几种终止下载的方式哈
        1、正常结束，即完整下载正常结束
        2、没有搜索到数据结束
        3、数据没有到限制，直接将数据下载完成结束
        4、shodan那边的数据量太大，这边连着喝多页都下载出错结束
        :return:
        """
        try:
            # for data in self._vpndata():
            #     yield data

            print("Start")
            for data in self._airosdata():
                yield data

            print("OK")
        except Exception as e:
            self._logger.error("Shodan download data error: {}".format(
                traceback.format_exc()))

    def _airosdata(self) -> iter:
        try:
            # # 数据库保存page
            page_start = int(self.task.cmd.stratagyscan.search.index)
            # # 需要单独去搜索ip的详细信息
            ips = {}
            queries = [
                'wordpress'
            ]
            for data in self._query_data(queries):
                yield data

        except Exception as e:
            self._logger.error("Shodan download AirOS data error: {}".format(
                traceback.format_exc()))

    def _vpndata(self) -> iter:
        try:
            # # 需要单独去搜索ip的详细信息
            ips = {}
            countries = [
                'LK', 'MV', 'PK', 'IN', 'BD', 'NP', 'BT', 'VN', 'LA', 'KH',
                'MM', 'TH', 'MY', 'SG', 'ID', 'PH', 'BN', 'TL'
            ]
            queries = [
                'http.favicon.hash:-1272756243 country:',
                'http.title:"Citrix Login" country:',
                'http.waf:"Citrix NetScaler" country:',
                'http.waf:"Citrix NetScaler" country:',
                '''ssl.cert.serial:1 ssl.cert.subject.cn:"default" ssl.cert.issuer.cn:"default" !ssl.cert.subject.cn:'iDRAC7 default certificate' !ssl.cert.subject.cn:'iDRAC6 default certificate' country:'''
            ]

            for q in queries:
                for c in countries:
                    for data in self._query_data([
                            q + c,
                    ]):
                        yield data

        except Exception as e:
            self._logger.error("Shodan download VPN data error: {}".format(
                traceback.format_exc()))

    def _query_data(self, queries: list, taskid: str = None, ips: dict = {}) -> iter:
        try:
            if not isinstance(taskid, str):
                taskid = str(uuid1())
            self.task.taskid = taskid
            self._logger.info("Shodan start with taskid: {}".format(taskid))

            # # 数据库保存page
            page_start = int(self.task.cmd.stratagyscan.search.index)
            url: str = None
            for query in queries:
                try:
                    # shodan的page默认值是1
                    page_start = 1
                    # page_start += 1
                    # querys = 'port:10001 xs5.ar2313'
                    # querys = self._get_cmd_fileter(self.query)
                    # if querys == '':
                    #     self._logger.info('No shodan query criteria match')
                    #     return
                    # shodan 查询应该是不得需要了的
                    total = 0
                    self.count = 0
                    self.page_error_times = 0
                    while True:
                        try:
                            # 只在这里判断连续出错次数
                            if self.page_error_times > self.error_limit:
                                self._write_iscantaskback(
                                    ECommandStatus.Dealing, '下载搜索结果，进度:100%')
                                break

                            # ---------------------------------------组装url
                            url = f'{self._basic_url}/shodan/host/search?key={self.apikey}&query={query}&page={page_start}'
                            self._logger.debug(f'Query url:{url}')
                            html = self._get_shodan_resultjson(url)
                            if html is None:
                                # 这里是一页出错，连续出错配置的次数就不再去访问这页了
                                self.page_error_times += 1
                                continue
                            s_dict: dict = json.loads(html)
                            if s_dict.__contains__('error'):
                                ex = s_dict.get('error')
                                # 这个error表示的是shodan的api报错了目前拿不到东西
                                # 或者是东西已经拿完了所以不用再继续了,所以shodan的error就直接退出了, 但是shodan
                                # 1、先表明这是什么错
                                self._logger.info(
                                    f'Shodan server error, error:{ex}')
                                # 2、如果是查询错误，就是服务器超时那么就尝试
                                # if 'request timed out' in ex:
                                self.page_error_times += 1
                                # 服务器内部的错，表明这页的访问有问题，那么就不再去访问这页，by swm 191231
                                continue

                            matches = s_dict.get('matches')
                            # shodan给的数据总数
                            total = int(s_dict.get('total', 0))
                            if len(matches) == 0 or total == 0:
                                # 这里表示没有查询到数据
                                self._logger.error(
                                    f'Shodan queried nothing\ncheck url:{url}\nshodan total result:{total}'
                                )
                                break

                            for match in matches:
                                res = self._parse_dict(match, page_start, ips)
                                # 这么加的话结果只会多不会少
                                self.count += 1
                                if res is not None:
                                    # 如果需要严格按着count_limit来，那么就会在这加上判断
                                    yield res.__dict__

                            # 当拿到一页的数据就产生一次任务回馈
                            progress = round(
                                self.count * 100 / self.count_limit, 2)
                            if progress > 100: progress = 100
                            self.task.progress = progress
                            self._write_iscantaskback(
                                ECommandStatus.Dealing,
                                f'下载搜索结果，进度:{progress}%')

                            # shodan每页100条,这样表示数据已经下载完成
                            if total < 100:
                                self._write_iscantaskback(
                                    ECommandStatus.Dealing, '下载搜索结果，进度:100%')
                                break

                            # 成功下载将出错次数清0
                            self.page_error_times = 0
                        except json.decoder.JSONDecodeError as err:
                            # 网络错误已经在查询的时候排除了，这里就只会剩下解析错误
                            self._logger.error(
                                f'Cant decode shodan json data\nError Url:{url}\nError info:{err}'
                            )
                            self.page_error_times += 1
                        finally:
                            # 只在这里翻页
                            page_start += 1
                            time.sleep(1)
                            # -----------判断是否应该结束
                            print(f'Get {self.count} data')
                            if self.count >= total:
                                break
                except Exception as ee:
                    self._logger.error(
                        "Shodan query data of one page error: {}".format(
                            traceback.format_exc()))

            for ip in ips.keys():
                with open('./allips.txt', 'a', encoding='utf-8') as fp:
                    fp.write(ip + '\n')

        except Exception as e:
            self._logger.error("Shodan query data error: {}".format(
                traceback.format_exc()))

    def _get_ips_detail(self):
        try:
            # 上面搜索结果结束之后去下载ip的信息
            # folder = Path(
            #     r'F:\WorkSpace\_Datas\airos\shodan_airos_IN_all_0819')
            # taskid = None
            # ips = {}
            # for fi in folder.iterdir():
            #     # file_path = Path(r"E:\swmdata\downloadshodandata\ips.json")
            #     if not fi.suffix.endswith("iscan_search"):
            #         continue
            #     file_path: Path = fi
            #     res = file_path.read_text(encoding='utf-8')

            #     sj: dict = json.loads(res)
            #     if taskid is None:
            #         taskid = sj.get("taskid")

            #     ip = sj.get("ip")
            #     ips[ip] = 1
            # ips = json.loads(res)

            ips = {"192.34.55.200": 1}

            self._logger.info('Start get every ip info')
            for i_f in self._download_ip_info(ips):
                yield i_f
        except Exception as e:
            self._logger.error("Shodan query ip detail error: {}".format(
                traceback.format_exc()))

    def _make_unshodata(self, banner: dict):
        """
        根据一条shodan数据来制作一条数据的唯一标识
        :param banner:
        :return:
        """
        ip = banner.get('ip_str')
        # 过滤数据数据格式为 ip:port
        rport = banner.get('port')
        # 去重需要，后期换了redis或者其他策略再去重吧
        unshodandata = f'{ip}:{rport}'

        timestamp: str = banner.get('timestamp', None)
        if timestamp is not None:
            timestamp = timestamp.replace('T', ' ')
        return unshodandata, timestamp

    def _download_all_data(self) -> iter:
        """
        下载所有的数据新增功能，常用于下载整个国家的数据
        需要支持重启继续下载
        country:TW before:30/12/2019
        :return:
        """
        # 1、获取当前存储的日期
        if self.task.query_date is None:
            qdate = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%d/%m/%Y')
        else:
            qdate = self.task.query_date

        if self.task.query_page is not None:
            page_start = self.task.query_page
        else:
            page_start = 1

        querys = self._get_cmd_fileter(self.query)
        if querys == '':
            self._logger.info('No shodan query criteria match')
            return
        # 查询所有数据需要将今天的日期加上，免得跑的太久了会有很多重复的数据
        # querys += f' after:{qdate}'
        # while True:
        #     try:
        #         # 只在这里判断连续出错次数
        #         if self.page_error_times > self.error_limit:
        #             self._write_iscantaskback(ECommandStatus.Dealing, '下载搜索结果，进度:100%')
        #             break
        #
        #         # ---------------------------------------组装url
        #         url = f'{self._basic_url}/shodan/host/search?key={self.apikey}&query={querys}&page={page_start}'
        #         self._logger.debug(f'Query url:{url}')
        #         html = self._get_shodan_resultjson(url)
        #         if html is None:
        #             # 这里是一页出错，连续出错配置的次数就不再去访问这页了
        #             self.page_error_times += 1
        #             continue
        #         s_dict: dict = json.loads(html)
        #         if s_dict.__contains__('error'):
        #             ex = s_dict.get('error')
        #             # 这个error表示的是shodan的api报错了目前拿不到东西
        #             # 或者是东西已经拿完了所以不用再继续了,所以shodan的error就直接退出了, 但是shodan
        #             # 1、先表明这是什么错
        #             self._logger.info(f'Shodan server error, error:{ex}')
        #             # 2、如果是查询错误，就是服务器超时那么就尝试
        #             # if 'request timed out' in ex:
        #             self.page_error_times += 1
        #             # 服务器内部的错，表明这页的访问有问题，那么就不再去访问这页，by swm 191231
        #             continue
        #
        #         matches = s_dict.get('matches')
        #         # shodan给的数据总数
        #         total = int(s_dict.get('total', 0))
        #         if len(matches) == 0 or total == 0:
        #             # 这里表示没有查询到数据
        #             self._logger.error(f'Shodan queried nothing\ncheck url:{url}\nshodan total result:{total}')
        #             break
        #         for match in matches:
        #             res = self._parse_dict(match, page_start)
        #             # 这么加的话结果只会多不会少
        #             self.count += 1
        #             if res is not None:
        #                 # 如果需要严格按着count_limit来，那么就会在这加上判断
        #                 yield res.__dict__
        #         # 成功下载将出错次数清0
        #         self.page_error_times = 0
        #         # 保存当前下载进度
        #         self._sqlfunc.update_iscan_query_data(qdate, page_start, self.task.taskid)
        #     except json.decoder.JSONDecodeError as err:
        #         # 网络错误已经在查询的时候排除了，这里就只会剩下解析错误
        #         self._logger.error(f'Cant decode shodan json data\nError Url:{url}\nError info:{err}')
        #         self.page_error_times += 1
        #     finally:
        #         # 只在这里翻页
        #         page_start += 1
        #         time.sleep(1)
        api = shodan.Shodan(self.apikey)
        try:
            total = api.count(querys)['total']
            self._logger.info(
                f"Will download {querys},about {total} pieces of data.")
            info = api.info()
        except Exception:
            raise Exception(
                'The Shodan API is unresponsive at the moment, please try again later.'
            )

        count = 0
        tries = 0

        results = {
            'matches': [True],
            'total': None,
        }

        while results['matches']:
            try:
                results = api.search(querys, minify=False, page=page_start)
                for banner in results['matches']:
                    # 对单独的一条数据进行处理
                    unshodanta, time_str = self._make_unshodata(banner)
                    if self._sqlfunc.is_shodandata_duplicate(
                            unshodanta, time_str):
                        continue
                    try:
                        res = self._parse_dict(banner, page_start)
                        self.count += 1
                        if res is not None:
                            self._sqlfunc.save_shodandata_identification(
                                unshodanta, time_str)
                            yield res.__dict__
                    except GeneratorExit:
                        return  # exit out of the function
                page_start += 1
                tries = 0
                self._sqlfunc.update_iscan_query_data(qdate, page_start,
                                                      self.task.taskid)
            except Exception as error:
                self._logger.error(f"Download data error ,err:{error}")
                # We've retried several times but it keeps failing, so lets error out
                if tries >= self.error_limit:
                    self._logger.error('Retry limit reached ({:d})'.format(
                        self.error_limit))
                    break
                tries += 1
            finally:
                time.sleep(
                    1
                )  # wait 1 second if the search errored out for some reason

        # 任务下载完成后删除数据库中保存的唯一标识
        self._sqlfunc.delete_shodan_table()
