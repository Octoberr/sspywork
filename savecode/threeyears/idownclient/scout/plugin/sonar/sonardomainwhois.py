"""
使用sonar查询domian的whois信息
create by judy 2019/07/16
"""
import datetime
import json
import traceback

import requests
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.iscoutdataset.iscouttask import IscoutTask
from idownclient.config_scouter import scouter_config
from ....clientdatafeedback.scoutdatafeedback import Whois, Email, Phone

logger: MsLogger = MsLogManager.get_logger("Sonarapidomainwhois")


class SonarDomainWhois(object):
    """domain whois search"""

    @classmethod
    def _make_email(cls, task: IscoutTask, level, email, reason):
        """
        当获取到了email的时候，会做一个email返回
        :param email:
        :return:
        """
        email_obj = Email(task, level, email)
        email_obj.reason = reason
        email_obj.source = 'Sonar system'
        return email_obj

    @classmethod
    def _make_phone(cls, task: IscoutTask, level, phone, reason):
        """
        当获取到了phone的时候会做一个phone返回
        :param phone:
        :return:
        """
        phone_obj = Phone(task, level, phone)
        phone_obj.reason = reason
        phone_obj.source = 'Sonar system'
        return phone_obj

    @staticmethod
    def get_whois_info(task: IscoutTask, level, domainname: str, reason):
        if not isinstance(task, IscoutTask):
            raise Exception("Invalid IscoutTask")
        if not isinstance(domainname, str):
            raise Exception("Invalid domain")
        try:
            url = f'{scouter_config.sonarapi}/dbs/domainwhois'
            headers = {
                'Accept': 'application/json'
            }
            querystring = {"domainName": domainname}
            response = requests.request("GET", url, headers=headers, params=querystring, timeout=10)
            res_text = response.text
            res_dict = json.loads(res_text)
            data = res_dict.get('data')
            if len(data) == 0:
                return
            data_res: dict = data[0]

            # registrantinfo
            registrantinfo: dict = data_res.get('registrant')
            if registrantinfo is None:
                # raise Exception(" Sonar registrant not found in whois info.")
                return

            registrant = registrantinfo.get('name')
            registrar = data_res.get('registrar')

            reg_time = data_res.get('creationDate')
            if reg_time is None or registrar is None:
                # raise Exception("Registtime not found in whois info")
                return

            registtime = datetime.datetime.fromtimestamp(
                int(reg_time)).strftime('%Y-%m-%d %H:%M:%S')
            whois: Whois = Whois(task, level, registrar, registtime)
            whois.registrant = registrant

            whois.registrantorg = registrantinfo.get('organization')
            # email 和 phone
            registrantemail = registrantinfo.get('email')
            if registrantemail is not None:
                whois.registrantemail = registrantinfo.get('email')
                emailobj = SonarDomainWhois._make_email(task, level, registrantemail, reason)
                yield emailobj
            registrantphone = registrantinfo.get('telephone')
            if registrantphone is not None:
                rphone = registrantphone.replace('.', '')
                if not rphone.startswith('+'):
                    rphone = '+' + rphone
                whois.registrantphone = rphone
                phoneobj = SonarDomainWhois._make_phone(task, level, rphone, reason)
                yield phoneobj

            # 拼接地址
            country = registrantinfo.get('country')
            state = registrantinfo.get('state')
            city = registrantinfo.get('city')
            street = registrantinfo.get('street1')
            addr = ''
            if country is not None:
                addr += f'{country}/'
            if state is not None:
                addr += f'{state}/'
            if city is not None:
                addr += f'{city}/'
            if street is not None:
                addr += f'{street}'
            whois.registrantaddr = addr

            dns = data_res.get('nameServers')
            if dns is not None:
                for d in dns.split('|'):
                    whois.set_dns_server(d.strip())

            update_time = data_res.get('updatedDate')
            if update_time is not None:
                whois.infotime = datetime.datetime.fromtimestamp(
                    int(update_time)).strftime('%Y-%m-%d %H:%M:%S')
            expire_time = data_res.get('expirationDate')
            if expire_time is not None:
                whois.expiretime = datetime.datetime.fromtimestamp(int(expire_time)).strftime('%Y-%m-%d %H:%M:%S')

            yield whois
        except:
            logger.error(
                f"Sonar api get domain whois error, please check sonar api connect, err:{traceback.format_exc()}")
