"""
使用phone来进行whois反查
"""
import datetime
import json
import traceback

import requests
from commonbaby.mslog import MsLogger, MsLogManager

from idownclient.clientdatafeedback.scoutdatafeedback import Whoisr
from idownclient.config_scouter import scouter_config

logger: MsLogger = MsLogManager.get_logger("Sonarapiphonewhoisr")


class SonarPhoneWhoisr(object):

    @staticmethod
    def get_whoisr(task, level, phone):
        """
        输入手机账号，返回sonar的反查信息
        :param phone:
        :return:
        """
        try:
            url = f'{scouter_config.sonarapi}/dbs/domainwhois/search'
            querystring = {"contactPhone": phone}
            headers = {
                'Accept': 'application/json'
            }
            response = requests.request("GET", url, headers=headers, params=querystring, timeout=10)
            res_text = response.text
            res_dict = json.loads(res_text)
            data = res_dict.get('data')
            if len(data) == 0:
                return
            for ew in data:
                domian = ew.get('domainName')
                if domian is None:
                    continue
                whoisr = Whoisr(task, level, domian)
                # registrant
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
        except:
            logger.error(f"Sonarapi get phonewhoisr error, please check sonar connect, err:{traceback.format_exc()}")
