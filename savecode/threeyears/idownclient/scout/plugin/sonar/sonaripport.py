"""
根据ip查开放的端口
create by judy 2019/07/17
"""
import json
import time

import requests

from idownclient.config_scouter import scouter_config

from ....clientdatafeedback.scoutdatafeedback import PortInfo


# -----------------------------------------------------已弃用
class SonarIpPort(object):
    @staticmethod
    def get_ip_port(task, level, ip):
        """
        去sonar查询ip，port
        :return:
        """
        pagelimit = 3000
        url = f'{scouter_config.sonarapi}/dbs/ports'
        # 如果数据太多了，是要带start继续查的
        querystring = {"ipFrom": ip, "ipTo": ip, "pageSize": pagelimit}
        headers = {
            'Accept': 'application/json'
        }
        errortimes = 0
        while True:
            try:
                response = requests.request("GET", url, headers=headers, params=querystring, timeout=10)
                res_text = response.text
                res_dict = json.loads(res_text)
                data = res_dict.get('data')
                data_num = len(data)
                if data_num == 0:
                    return None
                for data_one in data:
                    # host = data_one.get('ip')
                    port = data_one.get('port')
                    pobj = PortInfo(task, level, ip, port)
                    yield pobj
                # 这里判断下要不要继续翻页拿数据
                if data_num < pagelimit:
                    break
                else:
                    # 这里是拿最后一个data_one的timestamp,python嘛，动态语言就是这么玩的
                    querystring['start'] = data_one.get('timestamp')
            except:
                if errortimes > 10:
                    break
                errortimes += 1
                continue
            finally:
                time.sleep(1)
