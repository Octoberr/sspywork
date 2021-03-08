"""
根据邮箱账号来反查whoisr
"""
import datetime
import json
import traceback

import requests
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.iscoutdataset.iscouttask import IscoutTask
from idownclient.config_scouter import scouter_config
from ....clientdatafeedback.scoutdatafeedback import Whoisr

logger: MsLogger = MsLogManager.get_logger("Sonarapiemailwhoisr")


class SonarEmailWhoisr(object):
    """Sonar whoisr api"""

    @staticmethod
    def get_whoisr(task: IscoutTask, level: int, email: str):
        """
        这个暂时不翻页，它这个接口的翻页有问题，
        翻了也好像就没有数据了
        输入邮箱账号，返回sonar的反查信息
        :param email:
        :return: Whoisr
        """
        if not isinstance(task, IscoutTask):
            raise Exception("Invalid IscoutTask for sonar api whoisr")
        if not isinstance(email, str) or email == '':
            raise Exception("Invalid email for sonar api whoisr")

        try:
            url = f'{scouter_config.sonarapi}/dbs/domainwhois/search'
            headers = {
                'Accept': 'application/json'
            }
            querystring = {"contactEmail": email}
            response = requests.request("GET", url, headers=headers, params=querystring, timeout=10)
            res_text = response.text
            res_dict = json.loads(res_text)
            data = res_dict.get('data')
            if len(data) == 0:
                return
            for ew in data:
                domain = ew.get('domainName')
                if domain is None:
                    continue
                whoisr = Whoisr(task, level, domain)
                # registrant
                registrant = ew.get('registrant', {})
                name = registrant.get('name')
                if name is not None:
                    whoisr.registrant = name
                else:
                    whoisr.registrant = registrant.get('organization')

                # registrar呢？
                # 亲，api没有给呢
                # 看了下好像有,有的话赋一个值，没有就为None
                whoisr.registrar = ew.get('registrar')

                unix_time = ew.get('creationDate')
                whoisr.registtime = datetime.datetime.fromtimestamp(int(unix_time)).strftime('%Y-%m-%d %H:%M:%S')
                yield whoisr
        except:
            logger.error(f"Sonarapi get emailwhoisr error, please check sonar connect, err:{traceback.format_exc()}")
