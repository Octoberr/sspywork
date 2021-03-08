"""
whoissoft插件
查询whois信息
create by judy 2019/07/11
"""
import re

import requests

from datacontract.iscoutdataset import IscoutTask
from idownclient.clientdatafeedback.scoutdatafeedback import Whois, Email, Phone
from proxymanagement.proxymngr import ProxyMngr


class WhoisSoft(object):

    def __init__(self, task: IscoutTask):
        # iscout task用来构建回馈数据
        self.task = task
        self.web_url = 'http://whoissoft.com'
        self.ha = requests.session()
        # 初始化一些header和cookie
        self.ha.get(self.web_url)

    def _filter_a_lable(self, anystring):
        """
        去除<a>标签
        :param anystring:
        :return:
        """
        if '</a>' in anystring:
            res = re.sub('<a.+?>', '', anystring)
            return res.replace('</a>', '')
        else:
            return anystring

    def _make_email(self, level, email, reason):
        """
        当获取到了email的时候，会做一个email返回
        :param email:
        :return:
        """
        email_obj = Email(self.task, level, email)
        email_obj.reason = reason
        email_obj.source = 'http://whoissoft.com'
        return email_obj

    def _make_phone(self, level, phone, reason):
        """
        当获取到了phone的时候会做一个phone返回
        :param phone:
        :return:
        """
        phone_obj = Phone(self.task, level, phone)
        phone_obj.reason = reason
        phone_obj.source = 'http://whoissoft.com'
        return phone_obj

    def __format_phone(self, phone:str):
        """
        whois 上的phone不是那么标准
        类似于 +86.2321可能需要取点后面的值
        :param phone:
        :return:
        """
        if '.' in phone:
            return phone.replace('.', '')
        else:
            return phone

    def get_whoisres(self, level, domain, reason):
        """
        访问whois,然后获取结果
        :return:
        """
        # registrar
        re_registrar = re.compile('Registrar:(.+?)<br />')
        re_registraremail = re.compile('Registrar Abuse Contact Email: (.+?)<br />')
        re_registrarphone = re.compile('Registrar Abuse Contact Phone: (.+?)<br />')
        # registrant
        re_registrant_1 = re.compile('Registrant Name:(.+?)<br />')
        re_registrant_2 = re.compile('Registrant:(.+?)<br />')
        re_registrantorg = re.compile('Registrant Organization:(.+?)<br />')
        re_registrantemail = re.compile('Registrant Email:(.+?)<br />')
        re_registrantphone = re.compile('Registrant Phone:(.+?)<br />')
        # registrant addr
        # addr
        re_registrantcountry = re.compile('Registrant Country:(.+?)<br />')
        re_registrantSP = re.compile('Registrant State/Province:(.+?)<br />')
        re_registrantcity = re.compile('Registrant City:(.+?)<br />')
        re_registrantstreet = re.compile('Registrant Street:(.+?)<br />')
        # time
        re_registtime = re.compile('Creation Date:(.+?)<br />')
        re_expiretime = re.compile('Expiration.+?:(.+?)<br />')
        re_infotime = re.compile('Updated Date:(.+?)<br />')
        # dns
        re_dns = re.compile('Name Server:(.+?)<br />')

        url = f'{self.web_url}/{domain.strip()}'
        response = self.ha.get(url, proxies=ProxyMngr.get_static_proxy())
        res_string = response.text

        # 必要字段
        registrar = None
        registtime = None
        registrar_info = re_registrar.search(res_string)
        if registrar_info:
            registrar = self._filter_a_lable(registrar_info.group(1))

        registtime_info = re_registtime.search(res_string)
        if registtime_info:
            registtime = registtime_info.group(1).replace('T', ' ').replace('Z', '')
        # 如果必要字段没有的话，那么本次查询没有找到相应的数据，直接返回即可
        if registrar is None or registtime is None:
            return
        whois = Whois(self.task, level, registrar, registtime)

        registraremail_info = re_registraremail.search(res_string)
        if registraremail_info:
            registraremail = self._filter_a_lable(registraremail_info.group(1))
            whois.registraremail = registraremail
            # 这里要返回email
            d_email = self._make_email(level, registraremail, reason)
            yield d_email

        registrarphone_info = re_registrarphone.search(res_string)
        if registrarphone_info:
            registrarphone = self.__format_phone(registrarphone_info.group(1))
            whois.registrarphone = registrarphone
            # 这里要返回phone
            d_phone = self._make_phone(level, registrarphone, reason)
            yield d_phone

        registrant_2_info = re_registrant_2.search(res_string)
        if registrant_2_info:
            whois.registrant = self._filter_a_lable(registrant_2_info.group(1))
        else:
            registrant_1_info = re_registrant_1.search(res_string)
            if registrant_1_info:
                whois.registrant = registrant_1_info.group(1)

        registrantorg_info = re_registrantorg.search(res_string)
        if registrantorg_info:
            whois.registrantorg = self._filter_a_lable(registrantorg_info.group(1))

        registrantemail_info = re_registrantemail.search(res_string)
        if registrantemail_info:
            registrantemail = self._filter_a_lable(registrantemail_info.group(1))
            whois.registrantemail = registrantemail
            # 这里要返回email
            dt_email = self._make_email(level, registrantemail, reason)
            yield dt_email

        registrantphone_info = re_registrantphone.search(res_string)
        if registrantphone_info:
            registrantphone = self.__format_phone(registrantphone_info.group(1))
            whois.registrantphone = registrantphone
            # 这里也要返回phone
            dt_phone = self._make_phone(level, registrantphone, reason)
            yield dt_phone

        # 拼接地址
        country = None
        registrantcountry_info = re_registrantcountry.search(res_string)
        if registrantcountry_info:
            country = registrantcountry_info.group(1)
        sp = None
        registrantSP_info = re_registrantSP.search(res_string)
        if registrantSP_info:
            sp = registrantSP_info.group(1)
        city = None
        registrantcity_info = re_registrantcity.search(res_string)
        if registrantcity_info:
            city = registrantcity_info.group(1)
        street = None
        registrantstreet_info = re_registrantstreet.search(res_string)
        if registrantstreet_info:
            street = registrantstreet_info.group(1)
        addr = ''
        if country is not None:
            addr += f'{country}/'
        if sp is not None:
            addr += f'{sp}/'
        if city is not None:
            addr += f'{city}/'
        if street is not None:
            addr += f'{street}'
        whois.registrantaddr = addr

        # 最后就是时间了
        expiretime_info = re_expiretime.search(res_string)
        if expiretime_info:
            whois.expiretime = expiretime_info.group(1).replace('T', ' ').replace('Z', '')
        infotime_info = re_infotime.search(res_string)
        if infotime_info:
            whois.infotime = infotime_info.group(1).replace('T', ' ').replace('Z', '')
        dns_info = re_dns.findall(res_string)
        for el in dns_info:
            whois.set_dns_server(self._filter_a_lable(el))
        yield whois
