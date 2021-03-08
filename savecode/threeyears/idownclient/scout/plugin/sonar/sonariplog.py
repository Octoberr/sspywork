"""
使用sonar去下载domain的历史ip信息
create by judy 2019/07/17
"""
import datetime
import json
import time
import traceback

import requests
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import IscoutTask
from idownclient.clientdatafeedback.scoutdatafeedback import IP
from idownclient.config_scouter import scouter_config

logger: MsLogger = MsLogManager.get_logger("Sonarapiiplog")


class SonarIplog(object):

    @staticmethod
    def get_iplog(task: IscoutTask, level, domain):
        """
        去获取iplog
        :param domain_name:
        :return:
        """

        # pagelimit = 3000
        # 限制下，目前只去拿500条
        pagelimit = 500
        url = f'{scouter_config.sonarapi}/dbs/dns'
        querystring = {"domainName": domain, "pageSize": pagelimit}
        headers = {
            'Accept': 'application/json'
        }
        errortimes = 0
        while True:
            try:
                response = requests.request("GET", url, headers=headers, params=querystring, timeout=10)
                res_text = response.text
                res_dict = json.loads(res_text)
                data = res_dict.get('data', [])
                data_num = len(data)

                if data_num == 0:
                    return
                for el in data:
                    unix_logtime = el.get('timestamp')
                    ip_list = el.get('value')
                    date_logtime = datetime.datetime.fromtimestamp(int(unix_logtime)).strftime('%Y-%m-%d %H:%M:%S')
                    for ip in ip_list:
                        ipobj = IP(task, level, ip)
                        ipobj.logtime = date_logtime
                        yield ipobj

                # 目前因为数据量很大，所以限制下只返回500条
                task.success_count()
                break
                # 这里判断下要不要继续翻页拿数据
                # if data_num < pagelimit:
                #     break
                # else:
                # 这里是拿最后一个data_one的timestamp,python嘛，动态语言就是这么玩的
                # querystring['start'] = unix_logtime
            except:
                if errortimes > 3:
                    task.fail_count()
                    logger.error(
                        f"Sonarapi get iplog error, please check sonar api connect, error:{traceback.format_exc()}")
                    break
                errortimes += 1
                continue
            finally:
                time.sleep(1)
