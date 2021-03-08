"""
sonar的子域名查找
create by judy 2019/07/16
"""
import json
import time

import requests
import traceback

from datacontract import IscoutTask
from idownclient.clientdatafeedback.scoutdatafeedback import Domain
from idownclient.config_scouter import scouter_config
from commonbaby.mslog import MsLogger, MsLogManager

logger: MsLogger = MsLogManager.get_logger("Sonarapisubdomain")


class SonarSubdomain(object):

    @staticmethod
    def get_subdomain(task: IscoutTask, level, domian_name: str):
        """
        获取子域名
        :param domian_name:
        :return:
        """
        pagelimit = 500
        errortimes = 0
        url = f'{scouter_config.sonarapi}/dbs/domains/subdomains'
        headers = {
            'Accept': 'application/json'
        }
        querystring = {"domainName": domian_name, "pageSize": pagelimit}
        while True:
            try:
                response = requests.request("GET", url, headers=headers, params=querystring, timeout=10)
                res_text = response.text
                res_dict = json.loads(res_text)
                data = res_dict.get('data')
                data_num = len(data)
                if data_num == 0:
                    return
                for domain_one in data:
                    dobj = Domain(task, level, domain_one)
                    yield dobj

                # 限制500
                # 走到这里算成功
                task.success_count()
                break
                # 这里判断下要不要继续翻页拿数据
                # if data_num < pagelimit:
                #     break
                # else:
                # 这里是拿最后一个data_one的domain,python嘛，动态语言就是这么玩的
                # querystring['start'] = domain_one
            except:
                if errortimes > 3:
                    # 连续出错3次表示失败
                    task.fail_count()
                    logger.error(
                        f"Sonarapi get subdomain error, please check sonar api connect, err:{traceback.format_exc()}")
                    break
                errortimes += 1
                continue
            finally:
                time.sleep(1)
