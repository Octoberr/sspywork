"""
sonar的api，可能会有多个
"""
from .sonardomainlog import SonarDomainlog
from .sonardomainwhois import SonarDomainWhois
from .sonaremailwhoisr import SonarEmailWhoisr
from .sonargeoinfo import SonarGeoinfo
from .sonariplog import SonarIplog
# from .sonaripport import SonarIpPort
from .sonarphonewhoisr import SonarPhoneWhoisr
from .sonarsubdomain import SonarSubdomain
from .sonarkeywordwhoisr import SonarNetworkidWhoisr
from idownclient.scout.plugin.sonar.sonardomainwhoishistory import SonarDomainWhoisHistory


class SonarApi(object):

    @classmethod
    def domain_whois(cls, task, level, domain_name, reason):
        """
        sonar domain whois
        :param task:
        :param level:
        :param domain_name:
        :param reason:
        :return:
        """
        for d_o in SonarDomainWhois.get_whois_info(task, level, domain_name, reason):
            yield d_o

    @classmethod
    def domain_whoishistory(cls, task, level, domain_name, reason):
        """
        sonar domain whoishistory
        :param task:
        :param level:
        :param domain_name:
        :param reason:
        :return:
        """
        for d_h in SonarDomainWhoisHistory.get_whoishistory_info(task, level, domain_name, reason):
            yield d_h

    @classmethod
    def subdomains(cls, task, level, domain_name):
        """
        sonar domain subdomains
        :param task:
        :param level:
        :param domain_name:
        :return:
        """
        for d_o in SonarSubdomain.get_subdomain(task, level, domain_name):
            yield d_o

    @classmethod
    def iplogs(cls, task, level, domain):
        """
        sonar domian iplogs
        :param task:
        :param level:
        :param domain_name:
        :return:
        """
        for ip in SonarIplog.get_iplog(task, level, domain):
            yield ip

    @classmethod
    def email_whoisr(cls, task, level, email):
        """
        emailwhoisr反查
        :param task:
        :param level:
        :param email:
        :return:
        """
        for ew in SonarEmailWhoisr.get_whoisr(task, level, email):
            yield ew

    @classmethod
    def phone_whoisr(cls, task, level, phone):
        for pw in SonarPhoneWhoisr.get_whoisr(task, level, phone):
            yield pw

    @classmethod
    def domain_log(cls, task, level, ip):
        """
        使用ip去获取历史域名
        :param ip:
        :return:
        """
        for dl in SonarDomainlog.get_domainlog(task, level, ip):
            yield dl

    @classmethod
    def geoinfo(cls, task, level, ip):
        """
        使用ip获取geoinfo
        :param ip:
        :return:
        """
        ginfo = SonarGeoinfo.get_geoinfo(task, level, ip)
        return ginfo

    @classmethod
    def networkidwhoisr(cls, task, level, networkid):
        """
        使用networkid去sonar查whois
        :param task:
        :param level:
        :param networkid:
        :return:
        """
        for nwhoisr in SonarNetworkidWhoisr.get_whoisr(task, level, networkid):
            yield nwhoisr

    # @classmethod
    # def ipport(cls, task, level, ip):
    #     """
    #     已弃用
    #     使用ip获取开放的端口
    #     :param ip:
    #     :return:
    #     """
    #     for sip in SonarIpPort.get_ip_port(task, level, ip):
    #         yield sip
