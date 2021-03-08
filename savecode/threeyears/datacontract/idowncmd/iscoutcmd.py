"""
scout的设置也不是很多嘛
create by judy 2019/07/11

telegram流程更新，需要增加预置账号登陆和验证码收发
"""

from datetime import datetime
import re


class Function(object):
    def __init__(self, any_dict):
        self.function: dict = any_dict.get("function", {})
        if self.function is None:
            self.function = {}
        if not isinstance(self.function, dict):
            self.function = {}


class Port(object):
    def __init__(self, port, flag="tcp"):
        self.port = port
        self.flag = flag


class ProcessPort(object):
    @staticmethod
    def process_port(ports: list):
        """
        这个是需要支持端口段，[10,11,12-80]
        需要单独处理下端口
        :param ports:
        :return:
        """
        res = []
        # 默认的flag都是tcp
        flag = "tcp"
        for el in ports:
            if isinstance(el, str):
                # 判断是tcp还是udp
                if el.lower().startswith("u"):
                    flag = "udp"
                    port = el[el.index(":") + 1 :]
                else:
                    flag = "tcp"
                    port = el
                if "-" in port:
                    tmprange = port.split("-")
                    for rp in range(
                        int(tmprange[0].strip()), int(tmprange[1].strip()) + 1
                    ):
                        if rp > 65535:
                            continue
                        res.append(Port(rp, flag))
                else:
                    res.append(Port(int(port), flag))
            else:
                res.append(Port(int(el), flag))
        return res


########################################################
# domain
class SKF(object):
    def __init__(self, kf: dict):
        self.keywords = kf.get("keywords", [])
        if self.keywords is None:
            self.keywords = []
        self.filetypes = kf.get("filetypes", [])
        if self.filetypes is None:
            self.filetypes = []


class Searchengine(object):
    @property
    def sg_dict(self):
        return self.__sg_dict

    def __init__(self, sg: dict):
        self.__sg_dict = {}

        self.search_google: SKF = None
        __google = sg.get("search_google")
        if __google is not None:
            self.search_google = SKF(__google)

        self.search_bing: SKF = None
        __bing = sg.get("search_bing")
        if __bing is not None:
            self.search_bing = SKF(__bing)

        self.search_baidu: SKF = None
        __baidu = sg.get("search_baidu")
        if __baidu is not None:
            self.search_baidu = SKF(__baidu)

    def fill_searchengine(self, defds):
        # 没有默认值了, 所以也不需要再写更新
        if self.search_google is None:
            self.search_google: SKF = defds.search_google
        self.__sg_dict["search_google"] = self.search_google.__dict__

        if self.search_bing is None:
            self.search_bing: SKF = defds.search_bing
        self.__sg_dict["search_bing"] = self.search_bing.__dict__

        if self.search_baidu is None:
            self.search_baidu: SKF = defds.search_baidu
        self.__sg_dict["search_baidu"] = self.search_baidu.__dict__


"""
description: Scouter Domain 
param {*}
return {*}
"""


class CmdDomain(Function):
    """strategyscout.domain"""

    @property
    def enabled_subdomain(self) -> bool:
        if self.function.__contains__("subdomain") and self.function["subdomain"] == 0:
            return False
        return True

    @property
    def enabled_ip_history(self) -> bool:
        if (
            self.function.__contains__("ip_history")
            and self.function["ip_history"] == 0
        ):
            return False
        return True

    @property
    def enabled_whois(self) -> bool:
        if self.function.__contains__("whois") and self.function["whois"] == 0:
            return False
        return True

    @property
    def enabled_email(self) -> bool:
        if self.function.__contains__("email") and self.function["email"] == 0:
            return False
        return True

    @property
    def enabled_phone(self) -> bool:
        if self.function.__contains__("phone") and self.function["phone"] == 0:
            return False
        return True

    @property
    def enabled_searchgoogle(self) -> bool:
        if (
            self.function.__contains__("search_google")
            and self.function["search_google"] == 0
        ):
            return False
        return True

    @property
    def enabled_searchbing(self) -> bool:
        if (
            self.function.__contains__("search_bing")
            and self.function["search_bing"] == 0
        ):
            return False
        return True

    @property
    def enabled_searchbaidu(self) -> bool:
        if (
            self.function.__contains__("search_baidu")
            and self.function["search_baidu"] == 0
        ):
            return False
        return True

    @property
    def enabled_url(self) -> bool:
        if self.function.__contains__("url") and self.function["url"] == 0:
            return False
        return True

    @property
    def enabled_service(self) -> bool:
        if self.function.__contains__("service") and self.function["service"] == 0:
            return False
        return True

    @property
    def enabled_real_ip(self) -> bool:
        if self.function.__contains__("real_ip") and self.function["real_ip"] == 0:
            return False
        return True

    @property
    def enabled_side_site_detect(self) -> bool:
        if (
            self.function.__contains__("side_site_detect")
            and self.function["side_site_detect"] == 0
        ):
            return False
        return True

    @property
    def enabled_waf_detect(self) -> bool:
        if (
            self.function.__contains__("waf_detect")
            and self.function["waf_detect"] == 0
        ):
            return False
        return True

    @property
    def enabled_mail_server(self) -> bool:
        if (
            self.function.__contains__("mail_server")
            and self.function["mail_server"] == 0
        ):
            return False
        return True

    @property
    def domiandict(self):
        return self.__domain_dict

    def __init__(self, domain_dict: dict):
        Function.__init__(self, domain_dict)
        # self.searchengine_keywords: list = domain_dict.get(
        #     'searchengine_keywords')
        # self.searchengine_filetypes: list = domain_dict.get(
        #     'searchengine_filetypes')
        self.__domain_dict = {}

        self.searchengine: Searchengine = None
        __sgdict = domain_dict.get("searchengine")
        if __sgdict is not None:
            self.searchengine = Searchengine(__sgdict)

        ports: list = domain_dict.get("ports")
        if ports is None:
            ports = []
        self.ports = ProcessPort.process_port(ports)
        if not isinstance(self.ports, list):
            self.ports = []

        vuls = domain_dict.get("vuls", [])
        if vuls is None:
            vuls = []
        self.vuls = vuls

    def fill_defdomian(self, defdomain):
        dfunction: dict = defdomain.function.copy()
        # update 不会返回任何值，所以需要赋值
        dfunction.update(self.function)
        self.function: dict = dfunction
        self.__domain_dict["function"] = self.function

        if len(self.ports) == 0:
            self.ports = defdomain.ports
        self.__domain_dict["ports"] = self.ports

        if len(self.vuls) == 0:
            self.vuls = defdomain.vuls
        self.__domain_dict["vuls"] = self.vuls

        # if self.searchengine_keywords is None:
        #     self.searchengine_keywords: list = defdomian.searchengine_keywords
        # if self.searchengine_filetypes is None:
        #     self.searchengine_filetypes: list = defdomian.searchengine_filetypes
        if self.searchengine is None:
            self.searchengine: Searchengine = defdomain.searchengine
        else:
            self.searchengine.fill_searchengine(defdomain.searchengine)
        self.__domain_dict["searchengine"] = self.searchengine.sg_dict


########################################################
"""
description: Scouter IP 
param {*}
return {*}
"""


class CmdIP(Function):
    """strategyscout.ip"""

    @property
    def enabled_domain_detect(self) -> bool:
        if (
            self.function.__contains__("domain_detect")
            and self.function["domain_detect"] == 0
        ):
            return False
        return True

    @property
    def enabled_domain_history(self) -> bool:
        if (
            self.function.__contains__("domain_history")
            and self.function["domain_history"] == 0
        ):
            return False
        return True

    @property
    def enabled_location(self) -> bool:
        if self.function.__contains__("location") and self.function["location"] == 0:
            return False
        return True

    @property
    def enabled_ipwhois(self) -> bool:
        if self.function.__contains__("ipwhois") and self.function["ipwhois"] == 0:
            return False
        return True

    @property
    def enabled_url(self) -> bool:
        if self.function.__contains__("url") and self.function["url"] == 0:
            return False
        return True

    @property
    def enabled_service(self) -> bool:
        if self.function.__contains__("service") and self.function["service"] == 0:
            return False
        return True

    @property
    def enabled_side_site_detect(self) -> bool:
        if (
            self.function.__contains__("side_site_detect")
            and self.function["side_site_detect"] == 0
        ):
            return False
        return True

    @property
    def enabled_rangec_detect(self) -> bool:
        if (
            self.function.__contains__("rangec_detect")
            and self.function["rangec_detect"] == 0
        ):
            return False
        return True

    def __init__(self, ip_dict: dict):
        Function.__init__(self, ip_dict)

        ports: list = ip_dict.get("ports")
        if ports is None:
            ports = []
        self.ports = ProcessPort.process_port(ports)
        if self.ports is None:
            self.ports = []

        vuls = ip_dict.get("vuls", [])
        if vuls is None:
            vuls = []
        self.vuls = vuls

    def fill_defip(self, defip):
        dfunction: dict = defip.function.copy()
        dfunction.update(self.function)
        self.function: dict = dfunction

        if self.ports is None or len(self.ports) == 0:
            self.ports: list = defip.ports

        if self.vuls is None or len(self.vuls) == 0:
            self.vuls: list = defip.vuls


########################################################
"""
description: Scouter Url 
param {*}
return {*}
"""


class CmdUrl(Function):
    """strategyscout.url"""

    @property
    def enabled_homepage_code(self) -> bool:
        if (
            self.function.__contains__("homepage_code")
            and self.function["homepage_code"] == 0
        ):
            return False
        return True

    @property
    def enabled_summary(self) -> bool:
        if self.function.__contains__("summary") and self.function["summary"] == 0:
            return False
        return True

    @property
    def enabled_homepage_screenshot(self) -> bool:
        if (
            self.function.__contains__("homepage_screenshot")
            and self.function["homepage_screenshot"] == 0
        ):
            return False
        return True

    @property
    def enabled_components(self) -> bool:
        if (
            self.function.__contains__("components")
            and self.function["components"] == 0
        ):
            return False
        return True

    @property
    def enabled_waf_detect(self) -> bool:
        if (
            self.function.__contains__("waf_detect")
            and self.function["waf_detect"] == 0
        ):
            return False
        return True

    def __init__(self, url_dict: dict):
        Function.__init__(self, url_dict)

    def fill_defurl(self, defurl):
        dfunction = defurl.function.copy()
        dfunction.update(self.function)
        self.function: dict = dfunction


########################################################
# email
class SS(object):

    # 开始和结束的属性
    def __init__(self, ss_dict: dict):
        self.start = ss_dict.get("start")
        self.stop = ss_dict.get("stop")


class TR(object):
    # 时间区间，以天数为区间
    def __init__(self, tr_dict: dict):
        self.timerange = tr_dict.get("timerange", 30)


class SIdex(object):
    @property
    def sindex_dict(self):
        return self.__sindx_dict

    def __init__(self, si_dict: dict):
        self.__sindx_dict = {}
        # land facebook的
        self.landing_facebook: SS = None
        __lf = si_dict.get("landing_facebook")
        if __lf is not None:
            self.landing_facebook = SS(__lf)
        # land twitter的
        self.landing_twitter: SS = None
        __lt = si_dict.get("landing_twitter")
        if __lt is not None:
            self.landing_twitter = SS(__lt)

        # land instgram的
        self.landing_instgram: SS = None
        __lt = si_dict.get("landing_instgram")
        if __lt is not None:
            self.landing_instgram = SS(__lt)

    def fill_sidex(self, defsidex):
        # 更新下这个功能，需要识别别人限制拿多少条
        if self.landing_facebook is None:
            self.landing_facebook = defsidex.landing_facebook
        self.__sindx_dict["landing_facebook"] = self.landing_facebook.__dict__

        if self.landing_twitter is None:
            self.landing_twitter = defsidex.landing_twitter
        self.__sindx_dict["landing_twitter"] = self.landing_twitter.__dict__


class EmailPostTime(object):
    @property
    def pt_dict(self):
        return self.__ptdict

    def __init__(self, pt_dict: dict):
        self.__ptdict = {}

        self.public_facebook: SS = None
        __pf_dict = pt_dict.get("public_facebook")
        if __pf_dict is not None:
            self.public_facebook = SS(__pf_dict)

        self.searchengine_keywords = pt_dict.get("searchengine_keywords")
        self.searchengine_filetypes = pt_dict.get("searchengine_filetypes")

    def fill_posttime(self, defposttime):
        if self.public_facebook is None:
            self.public_facebook = defposttime.public_facebook
        self.__ptdict["public_facebook"] = self.public_facebook.__dict__

        if self.searchengine_keywords is None:
            self.searchengine_keywords = defposttime.searchengine_keywords
        self.__ptdict["searchengine_keywords"] = self.searchengine_keywords

        if self.searchengine_filetypes is None:
            self.searchengine_filetypes = defposttime.searchengine_filetypes
        self.__ptdict["searchengine_filetypes"] = self.searchengine_filetypes


"""
description: Scouter Email 
param {*}
return {*}
"""


class CmdEmail(Function):
    """cmd email"""

    @property
    def enabled_mailserver(self) -> bool:
        if (
            self.function.__contains__("mail_server")
            and self.function["mail_server"] == 0
        ):
            return False
        return True

    @property
    def enabled_whois_reverse(self) -> bool:
        if (
            self.function.__contains__("whois_reverse")
            and self.function["whois_reverse"] == 0
        ):
            return False
        return True

    @property
    def enabled_phone(self) -> bool:
        if self.function.__contains__("phone") and self.function["phone"] == 0:
            return False
        return True

    @property
    def enabled_searchgoogle(self) -> bool:
        if (
            self.function.__contains__("search_google")
            and self.function["search_google"] == 0
        ):
            return False
        return True

    @property
    def enabled_searchbing(self) -> bool:
        if (
            self.function.__contains__("search_bing")
            and self.function["search_bing"] == 0
        ):
            return False
        return True

    @property
    def enabled_searchbaidu(self) -> bool:
        if (
            self.function.__contains__("search_baidu")
            and self.function["search_baidu"] == 0
        ):
            return False
        return True

    @property
    def enabled_landing_facebook(self) -> bool:
        if (
            self.function.__contains__("landing_facebook")
            and self.function["landing_facebook"] == 0
        ):
            return False
        return True

    @property
    def enabled_landing_messenger(self) -> bool:
        if (
            self.function.__contains__("landing_messenger")
            and self.function["landing_messenger"] == 0
        ):
            return False
        return True

    # @property
    # def enabled_public_facebook(self) -> bool:
    #     if self.function.__contains__(
    #             'public_facebook') and self.function['public_facebook'] == 0:
    #         return False
    #     return True
    #
    # @property
    # def enabled_public_messenger(self) -> bool:
    #     if self.function.__contains__(
    #             'public_messenger') and self.function['public_messenger'] == 0:
    #         return False
    #     return True

    @property
    def email_dict(self):
        return self.__email_dict

    def __init__(self, email_dict: dict):
        Function.__init__(self, email_dict)
        self.__email_dict = {}

        self.searchindex: SIdex = None
        __si_dict = email_dict.get("searchindex")
        if __si_dict is not None:
            self.searchindex = SIdex(__si_dict)

        self.posttime: EmailPostTime = None
        __pt_dict = email_dict.get("posttime")
        if __pt_dict is not None:
            self.posttime = EmailPostTime(__pt_dict)

        self.searchengine: Searchengine = None
        __se_dict = email_dict.get("searchengine")
        if __se_dict is not None:
            self.searchengine = Searchengine(__se_dict)

    def fill_defemail(self, defemail):
        dfunction = defemail.function.copy()
        dfunction.update(self.function)
        self.function: dict = dfunction
        self.__email_dict["function"] = self.function

        if self.searchindex is None:
            self.searchindex: SIdex = defemail.searchindex
        else:
            self.searchindex.fill_sidex(defemail.searchindex)
        self.__email_dict["searchindex"] = self.searchindex.sindex_dict

        if self.posttime is None:
            self.posttime: EmailPostTime = defemail.posttime
        else:
            self.posttime.fill_posttime(defemail.posttime)
        self.__email_dict["posttime"] = self.posttime.pt_dict

        if self.searchengine is None:
            self.searchengine: Searchengine = defemail.searchengine
        else:
            self.searchengine.fill_searchengine(defemail.searchengine)
        self.__email_dict["searchengine"] = self.searchengine.sg_dict


########################################################
class PhonePostTime(object):
    @property
    def ppt_dict(self):
        return self.__pptdict

    def __init__(self, pt_dict: dict):
        self.__pptdict = {}

        self.public_telegram: SS = None
        __pf_dict = pt_dict.get("public_telegram")
        if __pf_dict is not None:
            self.public_telegram = SS(__pf_dict)

    def fill_posttime(self, defposttime):
        if self.public_telegram is None:
            self.public_telegram = defposttime.public_telegram
        self.__pptdict["public_telegram"] = self.public_telegram.__dict__


"""
description: Scouter Phone  
param {*}
return {*}
"""


class CmdPhone(Function):
    """"""

    @property
    def enabled_whois_reverse(self) -> bool:
        if (
            self.function.__contains__("whois_reverse")
            and self.function["whois_reverse"] == 0
        ):
            return False
        return True

    @property
    def enabled_email(self) -> bool:
        if self.function.__contains__("email") and self.function["email"] == 0:
            return False
        return True

    # @property
    # def enabled_phone(self) -> bool:
    #     if self.function.__contains__('phone') and self.function['phone'] == 0:
    #         return False
    #     return True
    @property
    def enabled_searchgoogle(self) -> bool:
        if (
            self.function.__contains__("search_google")
            and self.function["search_google"] == 0
        ):
            return False
        return True

    @property
    def enabled_searchbing(self) -> bool:
        if (
            self.function.__contains__("search_bing")
            and self.function["search_bing"] == 0
        ):
            return False
        return True

    @property
    def enabled_searchbaidu(self) -> bool:
        if (
            self.function.__contains__("search_baidu")
            and self.function["search_baidu"] == 0
        ):
            return False
        return True

    @property
    def enabled_landing_telegram(self) -> bool:
        if (
            self.function.__contains__("landing_telegram")
            and self.function["landing_telegram"] == 0
        ):
            return False
        return True

    @property
    def enabled_public_telegram(self) -> bool:
        if (
            self.function.__contains__("public_telegram")
            and self.function["public_telegram"] == 0
        ):
            return False
        return True

    @property
    def enabled_landing_messenger(self) -> bool:
        if (
            self.function.__contains__("landing_messenger")
            and self.function["landing_messenger"] == 0
        ):
            return False
        return True

    # @property
    # def enabled_public_messenger(self) -> bool:
    #     if self.function.__contains__(
    #             'public_messenger') and self.function['public_messenger'] == 0:
    #         return False
    #     return True

    @property
    def phone_dict(self):
        return self.__phone_dict

    def __init__(self, phone_dict):
        Function.__init__(self, phone_dict)
        self.__phone_dict = {}

        self.searchindex: SIdex = None
        __si_dict = phone_dict.get("searchindex")
        if __si_dict is not None:
            self.searchindex = SIdex(__si_dict)

        self.posttime: PhonePostTime = None
        __pt_dict = phone_dict.get("posttime")
        if __pt_dict is not None:
            self.posttime = PhonePostTime(__pt_dict)

        self.searchengine: Searchengine = None
        __se_dict = phone_dict.get("searchengine")
        if __se_dict is not None:
            self.searchengine = Searchengine(__se_dict)

    def fill_defphone(self, defphone):
        dfunction = defphone.function.copy()
        dfunction.update(self.function)
        self.function: dict = dfunction
        self.__phone_dict["function"] = self.function

        if self.searchindex is None:
            self.searchindex: SIdex = defphone.searchindex
        else:
            self.searchindex.fill_sidex(defphone.searchindex)
        self.__phone_dict["searchindex"] = self.searchindex.sindex_dict

        if self.posttime is None:
            self.posttime: PhonePostTime = defphone.posttime
        else:
            self.posttime.fill_posttime(defphone.posttime)
        self.__phone_dict["posttime"] = self.posttime.ppt_dict

        if self.searchengine is None:
            self.searchengine: Searchengine = defphone.searchengine
        else:
            self.searchengine.fill_searchengine(defphone.searchengine)
        self.__phone_dict["searchengine"] = self.searchengine.sg_dict


########################################################


class NidPostTime(object):
    @property
    def npt_dict(self):
        return self.__nptdict

    def __init__(self, pt_dict: dict):
        self.__nptdict = {}

        self.public_twitter: SS = None
        __pf_dict = pt_dict.get("public_twitter")
        if __pf_dict is not None:
            self.public_twitter = TR(__pf_dict)

    def fill_posttime(self, defposttime):
        if self.public_twitter is None:
            self.public_twitter = defposttime.public_twitter
        self.__nptdict["public_twitter"] = self.public_twitter.__dict__


"""
description: Scouter Networkid
param {*}
return {*}
"""


class CmdNetworkId(Function):
    """wat"""

    @property
    def enabled_whois_reverse(self) -> bool:
        if (
            self.function.__contains__("whois_reverse")
            and self.function["whois_reverse"] == 0
        ):
            return False
        return True

    @property
    def enabled_searchgoogle(self) -> bool:
        if (
            self.function.__contains__("search_google")
            and self.function["search_google"] == 0
        ):
            return False
        return True

    @property
    def enabled_searchbing(self) -> bool:
        if (
            self.function.__contains__("search_bing")
            and self.function["search_bing"] == 0
        ):
            return False
        return True

    @property
    def enabled_searchbaidu(self) -> bool:
        if (
            self.function.__contains__("search_baidu")
            and self.function["search_baidu"] == 0
        ):
            return False
        return True

    @property
    def enabled_email(self) -> bool:
        if self.function.__contains__("email") and self.function["email"] == 0:
            return False
        return True

    @property
    def enabled_phone(self) -> bool:
        if self.function.__contains__("phone") and self.function["phone"] == 0:
            return False
        return True

    @property
    def enabled_landing_facebook(self) -> bool:
        if (
            self.function.__contains__("landing_facebook")
            and self.function["landing_facebook"] == 0
        ):
            return False
        return True

    @property
    def enabled_landing_twitter(self) -> bool:
        if (
            self.function.__contains__("landing_twitter")
            and self.function["landing_twitter"] == 0
        ):
            return False
        return True

    @property
    def enabled_landing_linkedin(self) -> bool:
        if (
            self.function.__contains__("landing_linkedin")
            and self.function["landing_linkedin"] == 0
        ):
            return False
        return True

    @property
    def enabled_landing_instgram(self) -> bool:
        if (
            self.function.__contains__("landing_instgram")
            and self.function["landing_instgram"] == 0
        ):
            return False
        return True

    @property
    def enabled_public_facebook(self) -> bool:
        if (
            self.function.__contains__("public_facebook")
            and self.function["public_facebook"] == 0
        ):
            return False
        return True

    @property
    def enabled_public_twitter(self) -> bool:
        if (
            self.function.__contains__("public_twitter")
            and self.function["public_twitter"] == 0
        ):
            return False
        return True

    @property
    def enabled_public_linkedin(self) -> bool:
        if (
            self.function.__contains__("public_linkedin")
            and self.function["public_linkedin"] == 0
        ):
            return False
        return True

    @property
    def enabled_public_instgram(self) -> bool:
        if (
            self.function.__contains__("public_instgram")
            and self.function["public_instgram"] == 0
        ):
            return False
        return True

    @property
    def nid_dict(self):
        return self.__nid_dict

    def __init__(self, nid_dict: dict):
        Function.__init__(self, nid_dict)
        self.__nid_dict = {}
        # self.netidinfo: list = nid_dict.get('netidinfo')
        self.netidinfo: dict = {}
        nidinfotmp = nid_dict.get("netidinfo")
        if isinstance(nidinfotmp, list) and len(nidinfotmp) > 0:
            for d in nidinfotmp:
                # 这里判断一下，因为前端的模板为{'source': None, 'userid': None, 'url': None}
                # 所以当value全为None的时候就把当前这条数据删除, by judy 2020/02/18
                eldict = {k: v for k, v in d.items() if v is not None}
                if len(eldict) == 0:
                    continue
                # 先这样，有问题再说
                src = d.get("source")
                # 当进行public或者landing操作的时候source不能为空,那下面这句话就不需要了呀
                # if (src is None or src == "") and (
                #         self.enabled_landing_facebook or self.enabled_landing_instgram or self.enabled_landing_linkedin
                #         or self.enabled_landing_twitter or self.enabled_public_facebook or self.enabled_public_instgram
                #         or self.enabled_public_twitter or self.enabled_public_linkedin):
                #     raise Exception("Missing 'source' in cmd-netidinfo")
                userid = d.get("userid")
                userurl = d.get("url")
                n: NetidInfo = NetidInfo(src, userid, userurl)
                self.netidinfo[src] = n

        self.searchindex: SIdex = None
        __si_dict = nid_dict.get("searchindex")
        if __si_dict is not None:
            self.searchindex = SIdex(__si_dict)

        self.posttime: NidPostTime = None
        __pt_dict = nid_dict.get("posttime")
        if __pt_dict is not None:
            self.posttime = NidPostTime(__pt_dict)

        self.searchengine: Searchengine = None
        __se_dict = nid_dict.get("searchengine")
        if __se_dict is not None:
            self.searchengine = Searchengine(__se_dict)

    def fill_defnid(self, defnid):
        dfunction = defnid.function.copy()
        dfunction.update(self.function)
        self.function: dict = dfunction
        self.__nid_dict["function"] = self.function

        if self.netidinfo is None:
            self.netidinfo = defnid.netidinfo
        self.__nid_dict["netidinfo"] = self.netidinfo

        if self.searchindex is None:
            self.searchindex: SIdex = defnid.searchindex
        else:
            self.searchindex.fill_sidex(defnid.searchindex)
        self.__nid_dict["searchindex"] = self.searchindex.sindex_dict

        if self.posttime is None:
            self.posttime: NidPostTime = defnid.posttime
        else:
            self.posttime.fill_posttime(defnid.posttime)
        self.__nid_dict["posttime"] = self.posttime.npt_dict

        if self.searchengine is None:
            self.searchengine: Searchengine = defnid.searchengine
        else:
            self.searchengine.fill_searchengine(defnid.searchengine)
        self.__nid_dict["searchengine"] = self.searchengine.sg_dict


########################################################
# landing/public searchindex

_NetworkId_Functions = [
    "landing_facebook",
    "landing_messenger",
    "landing_telegram",
    "public_facebook",
    "public_messenger",
    "public_telegram",
    "public_twitter",
    "public_linkedin",
    "public_instgram",
]


class SearchIndex:
    """表示某个 function 的searchindex"""

    def __init__(self, name: str, idxstart: int = 0, idxstop: int = 10):
        if not isinstance(name, str) or not name in _NetworkId_Functions:
            raise Exception("Invalid function for setting searchindex")
        if not isinstance(idxstart, int) or idxstart < 0:
            raise Exception("Invalid indexstart for searchindex")
        if not isinstance(idxstop, int) or idxstop < idxstart:
            raise Exception("Invalid indexstart for searchindex")
        self._name: str = name
        self._idxstart: int = idxstart
        self._idxstop: int = idxstop


class CmdSearchIndex:
    """searchindex"""

    def __init__(self, dic: dict):
        if not isinstance(dic, dict):
            raise Exception("Invalid searchindex dict")

        self._searchindexes: dict = {}
        for k, v in dic.items():
            if not k in _NetworkId_Functions:
                raise Exception("Invalid function for setting searchindex")
            if not isinstance(v, dict):
                continue
            for sk, sv in v.items():
                idxstart: int = 0
                idxstop: int = 10
                if sk == "start":
                    idxstart = int(sv)
                elif sk == "stop":
                    idxstop = int(sv)
                self._searchindexes[k] = SearchIndex(k, idxstart, idxstop)


########################################################
# posttime


class Posttime:
    """表示一个NetworkId侦查的posttime设置"""

    def __init__(self, name: str, poststart: str = None, poststop: str = None):
        if not isinstance(name, str) or not name in _NetworkId_Functions:
            raise Exception("Invalid function for setting searchindex")
        if not isinstance(poststart, str):
            raise Exception("Invalid poststart for searchindex")
        if not isinstance(poststop, str):
            raise Exception("Invalid poststop for searchindex")
        self._name: str = name
        self._poststart_str: str = poststart
        self._poststart: datetime = datetime.strptime(poststart, "%Y-%m-%d %H:%M:%S")
        self._poststop_str: str = poststop
        self._poststop: datetime = datetime.strptime(poststop, "%Y-%m-%d %H:%M:%S")


class CmdPosttime:
    def __init__(self, dic: dict):
        if not isinstance(dic, dict):
            raise Exception("Invalid posttime dict")

        self._posttimes: dict = {}
        for k, v in dic.items():
            if not k in _NetworkId_Functions:
                raise Exception("Invalid function for setting posttime")
            if not isinstance(v, dict):
                raise Exception("Invalid function for setting posttime start/stop")
            for sk, sv in v.items():
                idxstart: int = 0
                idxstop: int = 10
                if sk == "start":
                    idxstart = int(sv)
                elif sk == "stop":
                    idxstop = int(sv)
                self._posttimes[k] = Posttime(k, idxstart, idxstop)


########################################################
# netidinfo

_NetworkId_Sources = [
    "facebook",
    "messenger",
    "telegram",
    "twitter",
    "linkedin",
    "instgram",
]


class NetidInfo:
    """表示网络Id侦查相关的netidinfo配置项"""

    def __init__(self, source: str, userid: str, url: str):
        # if not isinstance(source, str) or not source in _NetworkId_Sources:
        #     raise Exception("Invalid netidinfo in cmd")
        self._source: str = source
        self._userid: str = userid
        self._url: str = url


class CmdNetidInfo:
    def __init__(self, netlist: list):
        if not isinstance(netlist, list) or len(netlist) < 1:
            return
        # netidinfo字典结构：<source,NetidInfo>
        self._netidinfo: dict = {}
        for net in netlist:
            if not isinstance(net, dict):
                continue
            try:
                source = net["source"]
                userid = net["userid"]
                url = net["url"]
                self._netidinfo[source] = NetidInfo(source, userid, url)
            except Exception:
                continue


##############################################
"""
description:新增scouter账号登陆下载等功能
这个设置目前在特定目标侦查只有telegram才需要，所以不做默认设置 
param {*}
return {*}
"""


class PreAccount(object):
    def __init__(self, padict: dict):
        if not isinstance(padict, dict) and padict.__len__() == 0:
            return
        # 1 facebook,2 twitter,3 telegram 目前只约定3种预置账号的登陆，目前只会使用telegram by judy 20201109
        __apptype = padict.get("apptype")
        if __apptype is None or __apptype == "":
            raise Exception("Preaccount apptype cant be none")
        self.apptype = __apptype

        # 1 账密登陆,2 短信登陆,3 cookie登陆  约定的三种登陆方式，目前只使用了短信登陆 by judy 20201109
        __logintype = padict.get("logintype")
        self.logintype = __logintype

        self.globaltelcode = padict.get("globaltelcode")
        self.phone = padict.get("phone")
        self.email = padict.get("email")
        self.account = padict.get("account")
        self.password = padict.get("password")
        self.cookie = padict.get("cookie")


"""
description: 新增接收验证码
param {*}
return {*}
"""


class SendCode(object):
    def __init__(self, scdict: dict):
        if not isinstance(scdict, dict) and scdict.__len__() == 0:
            return
        self.parentcmdid = scdict.get("parentcmdid")
        # 验证码或者是手机短信验证码
        __code = scdict.get("code")
        if __code is None or __code == "":
            raise Exception("Code cant be None")
        self.code = __code


########################################################
"""
description: Scouter scout
param {*}
return {*}
"""


class StratagyScout(object):
    """特定策略"""

    @property
    def stratagyscout(self):
        """
        这里给出一份完整的scout的dict
        :return:
        """
        return self.__stratagyscout_dict

    def __init__(self, stratagyscout_json: dict):
        self.recursion_level = int(stratagyscout_json.get("recursion_level", 1))
        self.start_level = int(stratagyscout_json.get("start_level", 1))
        default_ports = stratagyscout_json.get("default_ports", [80, 443])
        if default_ports is None:
            default_ports = [20, 21, 22, 23, 25, 53, 80, 110, 143, 443, 3389, 8080]
        self.default_ports = ProcessPort.process_port(default_ports)
        # 新加字段relationfrom
        self.relationfrom = stratagyscout_json.get("relationfrom", None)

        # 侦查节点：
        self.cmddomain: CmdDomain = None
        _cmddomain = stratagyscout_json.get("domain")
        if not _cmddomain is None:
            self.cmddomain = CmdDomain(_cmddomain)

        self.cmdip: CmdIP = None
        _cmdip = stratagyscout_json.get("ip")
        if not _cmdip is None:
            self.cmdip = CmdIP(_cmdip)

        self.cmdurl: CmdUrl = None
        _cmdurl = stratagyscout_json.get("url")
        if not _cmdurl is None:
            self.cmdurl = CmdUrl(_cmdurl)

        self.cmdemail: CmdEmail = None
        _cmdemail = stratagyscout_json.get("email")
        if not _cmdemail is None:
            self.cmdemail = CmdEmail(_cmdemail)

        self.cmdphone: CmdPhone = None
        _cmdphone = stratagyscout_json.get("phone")
        if not _cmdphone is None:
            self.cmdphone = CmdPhone(_cmdphone)

        self.cmdnetworkid: CmdNetworkId = None
        _cmdnid = stratagyscout_json.get("networkid")
        if not _cmdnid is None:
            self.cmdnetworkid = CmdNetworkId(_cmdnid)

        # 新增预置账号登陆，by judy 2020/11/09
        _preaccount = stratagyscout_json.get("preaccount")
        if isinstance(_preaccount, dict) and _preaccount.__len__() > 0:
            self.preaccount = PreAccount(_preaccount)
        _sendcode = stratagyscout_json.get("sendcode")
        if isinstance(_sendcode, dict) and _sendcode.__len__() > 0:
            self.sendcode = SendCode(_sendcode)

        # 需要一份完整的json
        self.__stratagyscout_dict = stratagyscout_json

    def fill_defscout(self, defscout):
        if self.cmddomain is None:
            self.cmddomain = defscout.cmddomain
        else:
            self.cmddomain.fill_defdomian(defscout.cmddomain)
        self.__stratagyscout_dict["domain"] = self.cmddomain.domiandict

        if self.cmdip is None:
            self.cmdip = defscout.cmdip
        else:
            self.cmdip.fill_defip(defscout.cmdip)
        self.__stratagyscout_dict["ip"] = self.cmdip.__dict__

        if self.cmdurl is None:
            self.cmdurl: CmdUrl = defscout.cmdurl
        else:
            self.cmdurl.fill_defurl(defscout.cmdurl)
        # self.__stratagyscout_dict['url'] = self.cmdurl.__dict__

        if self.cmdemail is None:
            self.cmdemail: CmdEmail = defscout.cmdemail
        else:
            self.cmdemail.fill_defemail(defscout.cmdemail)
        self.__stratagyscout_dict["email"] = self.cmdemail.email_dict

        if self.cmdphone is None:
            self.cmdphone: CmdPhone = defscout.cmdphone
        else:
            self.cmdphone.fill_defphone(defscout.cmdphone)
        self.__stratagyscout_dict["phone"] = self.cmdphone.phone_dict

        if self.cmdnetworkid is None:
            self.cmdnetworkid: CmdNetworkId = defscout.cmdnetworkid
        else:
            self.cmdnetworkid.fill_defnid(defscout.cmdnetworkid)
        self.__stratagyscout_dict["networkid"] = self.cmdnetworkid.nid_dict
