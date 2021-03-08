"""
    使用sonar查询domian的WhoisHistory信息
"""
import datetime
import json
import re
import traceback

import requests
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import IscoutTask
from idownclient.clientdatafeedback.scoutdatafeedback import Email, Phone, Whois
from idownclient.config_scouter import scouter_config

logger: MsLogger = MsLogManager.get_logger("Sonarapidomainwhoishistory")


class SonarDomainWhoisHistory(object):
    """Domain WhoisHistory Search"""

    @classmethod
    def _make_email(cls, task: IscoutTask, level, email, reason):
        """
        当获取到email的时候,会做一个email返回.
        :param task:
        :param level:
        :param email:
        :param reason:
        :return:
        """
        email_obj = Email(task, level, email)
        email_obj.reason = reason
        email_obj.source = "Sonar system"
        return email_obj

    @classmethod
    def _make_phone(cls, task: IscoutTask, level, phone, reason):
        """
        当获取到phone的时候,会做一个phone返回.
        :param task:
        :param level:
        :param phone:
        :param reason:
        :return:
        """
        phone_obj = Phone(task, level, phone)
        phone_obj.reason = reason
        phone_obj.source = "Sonar system"
        return phone_obj

    @staticmethod
    def get_whoishistory_info(task: IscoutTask, level, domainName: str, reason):
        if not isinstance(task, IscoutTask):
            raise Exception("Invalid IscoutTask")
        if not isinstance(domainName, str):
            raise Exception("Invalid domain")

        # ①whois的历史版本号链接
        history_version_url = f'{scouter_config.sonarapi}/dbs/domainwhois/history'
        # (例: 'http://192.168.90.181:8080/sonar-restful-api/dbs/domainwhois/history?domainName=baidu.com')
        headers = {
            'Accept': 'application/json'
        }
        querystring = {"domainName": domainName}
        # Get request1
        response1 = requests.get(url=history_version_url, headers=headers, params=querystring, timeout=10)
        res_json = json.loads(response1.text)['data']  # 取到版本号列表
        if len(res_json) == 0:
            return

        li = []
        for da in res_json:  # 遍历版本号列表
            try:
                version = da['version']
                li.append(version)
                for ver in set(li):
                    # ②该version号下对应的whois详情信息
                    whois_detail_url = f'{scouter_config.sonarapi}/dbs/domainwhois?domainName={domainName}&version={ver}'
                    # (例: 'http://192.168.90.181:8080/sonar-restful-api/dbs/domainwhois?domainName=baidu.com&version=a163e61693e6c840')
                    # Get request2
                    response2 = requests.get(url=whois_detail_url)
                    whois_detail_datas = json.loads(response2.text)['data']
                    if len(whois_detail_datas) == 0:
                        return
                    detail_data: dict = whois_detail_datas[0]  # whois的详情信息

                    # 注册者的信息->dict
                    registrant_info: dict = detail_data['registrant']
                    if registrant_info is None:
                        return

                    registrar = detail_data['registrar']  # 1_注册商名称
                    registrant = registrant_info['name']  # 5_域名注册者名字
                    if registrant is None:  # 判断为空,就把organization赋给registrant
                        registrant = registrant_info['organization']
                    if registrant and registrant_info['organization'] is None:
                        return

                    registtime = detail_data['creationDate']  # 10_域名注册日期
                    if registtime is None or registrar is None:
                        return
                    registtime = datetime.datetime.fromtimestamp(int(registtime)).strftime('%Y-%m-%d %H:%M:%S')

                    # 调Whois类
                    whois: Whois = Whois(task, level, registrar, registtime)
                    whois.registrant = registrant  # 5_域名注册者名字
                    whois.registrantorg = registrant_info['organization']  # 6_域名注册者所属机构

                    registrantemail = registrant_info['email']  # 7_域名注册者邮箱
                    if registrantemail is not None:
                        whois.registrantemail = registrant_info['email']
                        emailobj = SonarDomainWhoisHistory._make_email(task, level, registrantemail, reason)
                        yield emailobj
                    registrantphone = registrant_info['telephone']  # 8_域名注册者电话
                    if registrantphone is not None:
                        whois.registrantphone = registrant_info['telephone']
                        phoneobj = SonarDomainWhoisHistory._make_phone(task, level, registrantemail, reason)
                        yield phoneobj

                    # 拼接地址 (9_域名注册者的地址)
                    country = registrant_info['country']
                    state = registrant_info['state']
                    city = registrant_info['city']
                    street = registrant_info['street1']
                    addr = ''
                    if country is not None:
                        addr += f'{country}/'
                    if state is not None:
                        addr += f'{state}/'
                    if city is not None:
                        addr += f'{city}/'
                    if street is not None:
                        addr += f'{street}/'
                    whois.registrantaddr = addr

                    expire_time = detail_data['expirationDate']  # 11_域名过期日期
                    if expire_time is not None:
                        whois.expiretime = datetime.datetime.fromtimestamp(int(expire_time)).strftime(
                            '%Y-%m-%d %H:%M:%S')
                    update_time = detail_data['updatedDate']  # 12_当前域名信息更新日期
                    if update_time is not None:
                        whois.infotime = datetime.datetime.fromtimestamp(int(update_time)).strftime('%Y-%m-%d %H:%M:%S')
                    dns = detail_data['nameServers']  # 13_域名DNS服务器列表
                    sp = re.split('[| \n]', dns.lower())
                    if dns is not None:
                        for d in sp:
                            whois.set_dns_server(d.strip())

                    yield whois

            except Exception as e:
                logger.error(f"Sonarapi get whoishistory error, please check out the sonar api connect, err:{traceback.format_exc()}")
