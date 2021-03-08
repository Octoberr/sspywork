"""
使用ip去查历史域名
create by judy 2019/07/17
"""
import datetime
import json
import time
import traceback
import pytz

import requests
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.iscoutdataset.iscouttask import IscoutTask
from ....clientdatafeedback.scoutdatafeedback import Domain
from ....config_scouter import scouter_config

logger: MsLogger = MsLogManager.get_logger("Sonarapidomainlog")


class SonarDomainlog(object):
    """domain: ip resolve history"""

    @staticmethod
    def get_domainlog(task: IscoutTask, level: int, ip: str):
        """
        去获取domainlog，历史解析ip
        :param level:
        :param task:
        :param ip:
        :return: IP
        """
        now_year = datetime.datetime.now(pytz.timezone('Asia/Shanghai')).year
        pagelimit = 500
        url = f'{scouter_config.sonarapi}/dbs/dnsrecords'
        headers = {
            'Accept': 'application/json'
        }
        querystring = {"ip": ip, "pageSize": pagelimit}
        errortime = 0
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
                    unix_time = el.get('timestamp')
                    domain_name = el.get('domainName')
                    if domain_name is None:
                        continue
                    # date_logtime = datetime.datetime.fromtimestamp(int(unix_time)).strftime('%Y-%m-%d %H:%M:%S')
                    date_logtime = datetime.datetime.fromtimestamp(int(unix_time))
                    log_year = date_logtime.year
                    if now_year - log_year >= scouter_config.iplog_time_limit:
                        continue
                    dobj = Domain(task, level, domain_name)
                    dobj.logtime = date_logtime.strftime('%Y-%m-%d %H:%M:%S')
                    yield dobj

                # 限制成500
                task.success_count()
                break
                # 这里判断下要不要继续翻页拿数据
                # if data_num < pagelimit:
                #     break
                # else:
                # 这里是拿最后一个data_one的timestamp,python嘛，动态语言就是这么玩的
                # querystring['start'] = domain_name
            except:
                if errortime > 3:
                    task.fail_count()
                    logger.error(f"Sonar get domain log error, check the sonar api connect,err:{traceback.format_exc()}")
                    break
                errortime += 1
                continue
            finally:
                time.sleep(1)
