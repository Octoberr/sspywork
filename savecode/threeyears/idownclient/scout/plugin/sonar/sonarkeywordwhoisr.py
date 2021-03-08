"""
networdid 的whoisr

"""

# -*- coding:utf-8 -*-

# 需要添加 通过注册人搜 whois反查信息
#

# 经询问，他没有直接用registrant搜的参数，直接使用contactName=xxx参数搜索，
# 他后台会自动匹配registrant.name=xxx的结果。
# import requests
# pagelimit = 30
# querystring = {"contactName": 'Merck Sharp and Dohme Corp', 'pageSize':pagelimit, 'pageNo':1}
# url = 'http://192.168.90.181:8080/sonar-restful-api/dbs/domainwhois/search'
# res = requests.get(url, params=querystring)
# print(res.text)
import datetime
import json
import time
import traceback

import requests
from commonbaby.mslog import MsLogger, MsLogManager

from idownclient.clientdatafeedback.scoutdatafeedback import Whoisr
from idownclient.config_scouter import scouter_config

logger: MsLogger = MsLogManager.get_logger("Sonarapikeywordwhoisr")


class SonarNetworkidWhoisr(object):

    @staticmethod
    def get_whoisr(task, level, networkid):
        """
        输入手机账号，返回sonar的反查信息
        :param networkid:
        :return:
        """
        pagelimit = 500
        pageno = 1
        url = f'{scouter_config.sonarapi}/dbs/domainwhois/search'
        headers = {
            'Accept': 'application/json'
        }
        querystring = {"contactName": networkid, 'pageSize': pagelimit, 'pageNo': pageno}
        errortimes = 0
        while True:
            try:
                response = requests.request("GET", url, headers=headers, params=querystring, timeout=10)
                res_text = response.text
                res_dict = json.loads(res_text)
                data = res_dict.get('data')
                # 拿到数据的总数
                data_num = len(data)
                if data_num == 0:
                    return
                for ew in data:
                    domian = ew.get('domainName')
                    if domian is None:
                        continue
                    whoisr = Whoisr(task, level, domian)
                    registrant = ew.get('registrant', {})
                    name = registrant.get('name')
                    if name is not None:
                        whoisr.registrant = name
                    else:
                        whoisr.registrant = registrant.get('organization')

                    whoisr.registrar = ew.get('registrar')
                    unix_time = ew.get('creationDate')
                    whoisr.registtime = datetime.datetime.fromtimestamp(int(unix_time)).strftime('%Y-%m-%d %H:%M:%S')
                    yield whoisr

                # 这里判断下要不要继续翻页拿数据
                # 限制查询数量500
                task.success_count()
                break
                # if data_num < pagelimit:
                #     break
                # else:
                # 这里是拿最后一个data_one的timestamp,python嘛，动态语言就是这么玩的
                # querystring['pageNo'] += 1
            except:
                if errortimes > 3:
                    task.fail_count()
                    logger.error(
                        f"Sonarapi get keywordwhoisr error, please check sonar connect, err:{traceback.format_exc()}")
                    break
                errortimes += 1
                continue
            finally:
                time.sleep(1)
