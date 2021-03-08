"""facebook search userid"""

# -*- coding:utf-8 -*-

import html as ht
import re
import time
import traceback
from urllib import parse
from datetime import datetime
import pytz

from bs4 import BeautifulSoup
from commonbaby.helpers import helper_str, helper_time
from lxml import etree

from datacontract.iscoutdataset import IscoutTask

from ....clientdatafeedback.scoutdatafeedback import NetworkProfile
from .fblogin import FBLogin

# 两次人员搜索之间的间隔时间（秒），搜太快会被 temporarily blocked.
search_interval: float = 2  # 秒
last_search_timestamp: int = -1  # 本地时间戳


def _check_interval(func):
    """检查两次搜索之间的间隔时间\n
    两次人员搜索之间的间隔时间（秒），搜太快会被 temporarily blocked."""
    def do_func(*args, **kwargs):
        currtimestamp = datetime.now(pytz.timezone('Asia/Shanghai')).timestamp()
        global last_search_timestamp
        while currtimestamp - last_search_timestamp < search_interval:
            time.sleep(0.1)

        last_search_timestamp = currtimestamp
        return func(*args, **kwargs)

    return do_func


class FBProfile(FBLogin):
    """facebook search userid"""

    # <img class="_11kf img" alt="Jake Paul's Profile Photo, Image may contain: 1 person, closeup" src="https://scontent-lax3-1.xx.fbcdn.net/v/t1.0-1/c1.0.160.160a/p160x160/69089536_111865926849430_92193792290979840_n.jpg?_nc_cat=102&amp;_nc_oc=AQmOEbgVHuR2C31L_ZG51XY0GeHY1vTlrIpFUexkKT_m0Em6xR3ezLSuOXFz-erCs14&amp;_nc_ht=scontent-lax3-1.xx&amp;oh=f267015344eb408f6b345f39c7cd2823&amp;oe=5E3273B4">
    _re_profile_photo = re.compile(
        '<img[^>]+?Profile Photo[^>]+?src="([^"]+?)".*?>', re.S)

    # re outer: key: Angelica Velasco
    _re_info = re.compile(r'<!--\s*?(<div>.*?</div>)\s-->', re.S)
    _re_info_relation = re.compile(
        r'<!--\s*?(<div[^!]+?(Family Members|家庭成员).*?</div>)\s*?-->', re.S)
    # _re_info_about = re.compile(
    #     r'<!--\s*?(<div[^!]+?(Other Names|Favorite Quotes|About )[^!]+?</div>)\s-->',
    #     re.S)
    _re_bio_othernames = re.compile(
        r'<!--\s*?(<div[^!]+?(Other Names)[^!]+?</div>)\s-->', re.S)
    _re_bio_favorites = re.compile(
        r'<!--\s*?(<div[^!]+?(Favorite Quotes)[^!]+?</div>)\s-->', re.S)
    _re_bio_about = re.compile(
        r'<!--\s*?(<div[^!]+?(About )[^!]+?</div>)\s-->', re.S)

    # re inner
    _re_edu_work = re.compile(
        r'<div.*?<span\s.*>?Work</span>\s*?</div>\s*?(<ul.*?/li>\s*?</ul>)\s*?</div',
        re.S)
    _re_edu_skill = re.compile(
        r'<div.*?<span\s.*>?Professional Skills</span>\s*?</div>\s*?(<ul.*?/li>\s*?</ul>)\s*?</div',
        re.S)
    _re_edu_edu = re.compile(
        r'<div.*?<span\s.*?>Education</span>\s*?</div>\s*?(<ul.*?/li>\s*?</ul>)\s*?</div',
        re.S)
    _re_living_home = re.compile(
        r'<div.*?<span\s.*?>Current City and Hometown</span>\s*?</div>\s*?(<ul.*?/li>\s*?</ul>)\s*?</div',
        re.S)
    _re_contact_info = re.compile(
        r'<div.*?<span\s.*?>Contact Information</span>\s*?</div>\s*?(<ul.*?/li>\s*?</ul>)\s*?</div',
        re.S)
    _re_contact_websites = re.compile(
        r'<div.*?<span\s.*?>Websites and Social Links</span>\s*?</div>\s*?(<ul.*?/li>\s*?</ul>)\s*?</div',
        re.S)
    _re_relation = re.compile(
        r'<div.*?<span\s.*?>Family Members</span>\s*?</div>\s*?(<ul.*?/li>\s*?</ul>)\s*?</div',
        re.S)

    def __init__(self, task: IscoutTask):
        super(FBProfile, self).__init__(task)

        # self._links_about: dict = {
        #     "overview": None,
        #     "education": None,
        #     "places": None,
        #     "contact_basic": None,
        #     "all_relationships": None,
        #     "about": None,
        #     "year_overviews": None,
        # }

####################################
# ensure user

    def _get_user_by_userid(self,
                            userid: str,
                            reason: str = None,
                            get_profile_pic: bool = True,
                            recursive: int = 0) -> NetworkProfile:
        """ensure a user by userid\n
        param recursive: 内部参数，不用管"""
        try:
            url: str = "https://www.facebook.com/profile.php?id={}".format(
                userid)
            return self._get_user_by_url(url,
                                         reason,
                                         get_profile_pic,
                                         recursive=recursive)

        except Exception:
            self._logger.error("Get user by userid error: {}".format(
                traceback.format_exc()))

    def _get_user_by_url(self,
                         userurl: str,
                         reason: str = None,
                         get_profile_pic: bool = False,
                         recursive: int = 0) -> NetworkProfile:
        """ensure the user by user url\n
        param recursive: 内部参数，不用管"""
        res: NetworkProfile = None
        try:
            html, redir = self._ha.getstring_unredirect(userurl,
                                                        headers="""
            accept: */*
            accept-encoding: gzip, deflate
            accept-language: en-US,en;q=0.9
            cache-control: no-cache
            content-type: application/x-www-form-urlencoded
            origin: https://www.facebook.com
            pragma: no-cache
            referer: https://www.facebook.com/search/people/?q={}&epa=SERP_TAB
            sec-fetch-mode: cors
            sec-fetch-site: same-origin
            user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36"""
                                                        )

            if not redir is None and not redir == "":
                html = self._ha.getstring(redir,
                                          headers="""
                accept: */*
                accept-encoding: gzip, deflate
                accept-language: en-US,en;q=0.9
                cache-control: no-cache
                content-type: application/x-www-form-urlencoded
                origin: https://www.facebook.com
                pragma: no-cache
                referer: https://www.facebook.com/search/people/?q={}&epa=SERP_TAB
                sec-fetch-mode: cors
                sec-fetch-site: same-origin
                user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36"""
                                          )
                userurl = redir

            if html is None:
                self._logger.error(
                    "Access user homepage failed: {}".format(userurl))
                return res

            if html.__contains__("You’re Temporarily Blocked"):
                # 被暂时屏蔽了，就递归等待，每次等10秒
                # 等待2分钟（120秒）还没好就放弃，返回None
                # 后面需要搞账号池来解决此问题？
                if recursive >= 12:
                    self._logger.info(
                        "Search too fast, You’re Temporarily Blocked over 120s, give up."
                    )
                    return None
                self._logger.info(
                    "Search too fast, You’re Temporarily Blocked, sleep 10s")
                time.sleep(10)
                recursive += 1
                res = self._get_user_by_url(userurl,
                                            reason=reason,
                                            get_profile_pic=get_profile_pic,
                                            recursive=recursive)
                return res

            # "entity_id":"100030846743121"
            # "profile_session_id":"100013325533097:100030846743121:1568721729"
            userid: str = None
            succ, userid = helper_str.substringif(html, 'entity_id":"', '"')
            if not succ:
                succ, userid = helper_str.substringif(html,
                                                      'profile_session_id":"',
                                                      '"')
                if not succ:
                    self._logger.error(
                        "Match userid failed: {}".format(userurl))
                    return res
                else:
                    userid = userid.split(':')[1]

            # type":"Person","name":"Jay Chou"
            username: str = None
            succ, username = helper_str.substringif(html,
                                                    'type":"Person","name":"',
                                                    '"')
            if not succ:
                self._logger.error("Match username failed: {}".format(userurl))
                return res

            res = NetworkProfile(username, userid, self._SOURCE)
            res.url = userurl
            if not reason is None:
                res.reason = reason
            else:
                res.reason = self._dtools.landing_facebook

            # profile photo
            if get_profile_pic:
                soup = BeautifulSoup(html.replace('<!--', '').replace('-->', ''), 'lxml')
                # photo
                photo = soup.select_one('._11kf.img')
                if photo:
                    try:
                        pic_url = photo.attrs['src'].replace('amp;', '')
                        pic = self._ha.get_response_stream(pic_url)
                        res._profile_pic = helper_str.base64bytes(pic.read())
                    except:
                        pass

        except Exception:
            self._logger.error("Get user by url error: {}".format(
                traceback.format_exc()))
        return res

####################################
# get profile detail

    @_check_interval
    def _get_profile_detail_userid(self,
                                   userid: str,
                                   reason: str = None,
                                   recursive: int = 0,
                                   get_profile_pic: bool = False
                                   ) -> NetworkProfile:
        """get user profile detail.\n
        param recursive: 内部参数，不用管"""
        try:
            url: str = "https://www.facebook.com/profile.php?id={}".format(
                userid)
            return self._get_profile_detail_userurl(
                url,
                reason,
                recursive=recursive,
                get_profile_pic=get_profile_pic)

        except Exception:
            self._logger.error("Get profile detail by userid error: {}".format(
                traceback.format_exc()))

    @_check_interval
    def _get_profile_detail_userurl(self,
                                    userurl: str,
                                    reason: str = None,
                                    recursive: int = 0,
                                    get_profile_pic: bool = False
                                    ) -> NetworkProfile:
        """get user profile detail.\n
        param recursive: 内部参数，不用管"""
        res: NetworkProfile = None
        try:

            res = self._get_user_by_url(userurl,
                                        reason,
                                        get_profile_pic=get_profile_pic,
                                        recursive=recursive)
            if not isinstance(res, NetworkProfile):
                return res

            res = self._get_profile_detail(res, reason, recursive=recursive)

            self._logger.info("Got user profile detail: {} {}".format(
                res.nickname, res.url))

        except Exception:
            self._logger.error(
                "Get profile detail of user: {} failed: {}".format(
                    userurl, traceback.format_exc()))
        return res

    @_check_interval
    def _get_profile_detail(self,
                            profile: NetworkProfile,
                            reason: str = None,
                            recursive: int = 0) -> NetworkProfile:
        """get user profile detail.\n
        param recursive: 内部参数，不用管"""
        try:
            if not isinstance(profile, NetworkProfile):
                self._logger.error(
                    "Invalid NetworkProfile for getting profile detail.")
                return None

            self._get_education(profile)
            self._get_living(profile)
            self._get_addrinfo(profile)
            self._get_relation(profile)
            self._get_bio(profile)

            self._logger.info("Got user profile detail: {} {}".format(
                profile.nickname, profile.url))

        except Exception:
            self._logger.error(
                "Get profile detail of user: {} failed: {}".format(
                    profile.url, traceback.format_exc()))
        return profile

###################################
# education

    def _get_education(self, profile: NetworkProfile):
        """教育工作信息"""
        try:
            url: str = "https://www.facebook.com/profile.php?id={}&sk=about&section=education&lst={}%3A{}%3A{}".format(
                profile._userid, self._userid, profile._userid,
                helper_time.ts_since_1970(10))

            html = self._ha.getstring(url,
                                      headers="""
            accept: */*
            accept-encoding: gzip, deflate
            accept-language: en-US,en;q=0.9
            cache-control: no-cache
            content-type: application/x-www-form-urlencoded
            origin: https://www.facebook.com
            pragma: no-cache
            referer: {}
            sec-fetch-mode: cors
            sec-fetch-site: same-origin""".format(profile.url))

            if html is None:
                return

            # m = self._re_info_work.search(html)
            m = self._re_info.search(html)
            if m is None:
                self._logger.debug("No education info found: {} {}".format(
                    profile.nickname, profile.url))
                return

            strdiv: str = m.group(1).strip()
            if not isinstance(strdiv, str) or strdiv == "":
                self._logger.debug("Get education info failed: {} {}".format(
                    profile.nickname, profile.url))
                return

            m = self._re_edu_work.search(strdiv)
            if not m is None:
                ulwork = m.group(1).strip()
                if not ulwork is None and ulwork != "":
                    self.__parse_edu_work(profile, ulwork)

            m = self._re_edu_skill.search(strdiv)
            if not m is None:
                ulskill = m.group(1).strip()
                if not ulskill is None and ulskill != "":
                    self.__parse_edu_skill(profile, ulskill)

            m = self._re_edu_edu.search(strdiv)
            if not m is None:
                uledu = m.group(1).strip()
                if not uledu is None and uledu != "":
                    self.__parse_edu_edu(profile, uledu)

        except Exception:
            self._logger.error(
                "Get education page failed: username:{} url:{}\nerror: {}".
                format(profile._networkid, profile.url,
                       traceback.format_exc()))

    def __parse_edu_work(self, profile: NetworkProfile, ul: str):
        """解析工作地"""
        try:

            hdoc: etree._Element = etree.XML(ul, etree.XMLParser())
            if hdoc is None:
                self._logger.error("Parse XML edu_work failed: {} {}".format(
                    profile.nickname, profile.url))
                return

            xlis = hdoc.findall('li')
            if xlis is None or len(xlis) < 1:
                return

            detail: dict = {}
            idx: int = 0
            for xli in xlis:
                try:
                    xli: etree._Element = xli
                    if xli is None:
                        continue
                    xdiv: etree._Element = xli.find('div/div/div/div/div[2]')
                    if xdiv is None:
                        continue
                    # url
                    xa: etree._Element = xdiv.find('div[1]/a')
                    if xa is None:
                        continue
                    workurl: str = xa.get('href')
                    if not workurl is None and workurl != "":
                        detail[f"工作{idx}url"] = workurl

                    # text
                    alltext = ";".join(xdiv.itertext())
                    if not alltext is None and alltext != "":
                        detail[f"工作{idx}"] = alltext

                except Exception as ex:
                    self._logger.debug(
                        "Parse one edu_work information failed: {} {} {}".
                        format(profile.nickname, profile.url, ex.args))
                finally:
                    idx += 1

            if len(detail) > 0:
                profile.set_details(**detail)

        except Exception:
            self._logger.error(
                "Parse edu_work failed: username:{} url:{}\nerror: {}".format(
                    profile._networkid, profile.url, traceback.format_exc()))

    def __parse_edu_skill(self, profile: NetworkProfile, ul: str):
        """解析工作地"""
        try:
            hdoc: etree._Element = etree.XML(ul, etree.XMLParser())
            if hdoc is None:
                self._logger.error("Parse XML edu_skill failed: {} {}".format(
                    profile.nickname, profile.url))
                return

            xlis = hdoc.findall('li')
            if xlis is None or len(xlis) < 1:
                return

            detail: dict = {}
            idx: int = 0
            for xli in xlis:
                try:
                    xli: etree._Element = xli
                    if xli is None:
                        continue
                    xas: etree._Element = xli.findall('.//a')
                    if xas is None or len(xas) < 1:
                        continue

                    for xa in xas:
                        try:
                            # url
                            skillurl: str = xa.get('href')
                            if not skillurl is None and skillurl != "":
                                detail[f"技能{idx}url"] = skillurl

                            # text
                            alltext = ";".join(xa.itertext())
                            if not alltext is None and alltext != "":
                                detail[f"技能{idx}"] = alltext

                        except Exception:
                            self._logger.debug(
                                "Parse one edu_skill failed: {} {} {}".format(
                                    profile.nickname, profile.url, ex.args))
                        finally:
                            idx += 1

                except Exception as ex:
                    self._logger.debug(
                        "Parse one edu_skill information failed: {} {} {}".
                        format(profile.nickname, profile.url, ex.args))

            if len(detail) > 0:
                profile.set_details(**detail)

        except Exception:
            self._logger.error(
                "Parse edu_skill failed: username:{} url:{}\nerror: {}".format(
                    profile._networkid, profile.url, traceback.format_exc()))

    def __parse_edu_edu(self, profile: NetworkProfile, ul: str):
        """解析工作地"""
        try:
            hdoc: etree._Element = etree.XML(ul, etree.XMLParser())
            if hdoc is None:
                self._logger.error("Parse XML edu_edu failed: {} {}".format(
                    profile.nickname, profile.url))
                return

            xlis = hdoc.findall('li')
            if xlis is None or len(xlis) < 1:
                return

            detail: dict = {}
            idx: int = 0
            for xli in xlis:
                try:
                    xli: etree._Element = xli
                    if xli is None:
                        continue
                    xdiv: etree._Element = xli.find('div/div/div/div/div[2]')
                    if xdiv is None:
                        continue
                    # url
                    xa: etree._Element = xdiv.find('div[1]/a')
                    if xa is None:
                        continue
                    schoolurl: str = xa.get('href')
                    if not schoolurl is None and schoolurl != "":
                        detail[f"学校{idx}url"] = schoolurl

                    # text
                    alltext = ";".join(xdiv.itertext())
                    if not alltext is None and alltext != "":
                        detail[f"学校{idx}"] = alltext

                except Exception as ex:
                    self._logger.debug(
                        "Parse one edu_edu information failed: {} {} {}".
                        format(profile.nickname, profile.url, ex.args))
                finally:
                    idx += 1

            if len(detail) > 0:
                profile.set_details(**detail)

        except Exception:
            self._logger.error(
                "Parse edu_edu failed: username:{} url:{}\nerror: {}".format(
                    profile._networkid, profile.url, traceback.format_exc()))

###################################
# living

    def _get_living(self, profile: NetworkProfile):
        """住址信息"""
        try:
            # education
            # https://www.facebook.com/profile.php?id=100030846743121&sk=about&section=overview&lst=100013325533097%3A100030846743121%3A1568790537

            url: str = "https://www.facebook.com/profile.php?id={}&sk=about&section=living&lst={}%3A{}%3A{}".format(
                profile._userid, self._userid, profile._userid,
                helper_time.ts_since_1970(10))

            html = self._ha.getstring(url,
                                      headers="""
            accept: */*
            accept-encoding: gzip, deflate
            accept-language: en-US,en;q=0.9
            cache-control: no-cache
            content-type: application/x-www-form-urlencoded
            origin: https://www.facebook.com
            pragma: no-cache
            referer: {}
            sec-fetch-mode: cors
            sec-fetch-site: same-origin""".format(profile.url))

            if html is None:
                return

            address = helper_str.substring(html, 'data-hovercard-prefer-more-content-show="1">', '<')
            if address:
                profile.address = address

        except Exception:
            self._logger.error(
                "Get education page failed: username:{} url:{}".format(
                    profile._networkid, profile.url))

    # 失效
    def __parse_living_home(self, profile: NetworkProfile, ul: str):
        """解析工作地"""
        try:
            hdoc: etree._Element = etree.XML(ul, etree.XMLParser())
            if hdoc is None:
                self._logger.error(
                    "Parse XML living_home failed: {} {}".format(
                        profile.nickname, profile.url))
                return

            xlis = hdoc.findall('li')
            if xlis is None or len(xlis) < 1:
                return

            detail: dict = {}
            idx: int = 0
            for xli in xlis:
                try:
                    xli: etree._Element = xli
                    if xli is None:
                        continue
                    xdiv: etree._Element = xli.find(
                        'div/div/div/div/div/div[2]')
                    if xdiv is None:
                        continue
                    # url
                    xa: etree._Element = xdiv.find('span/a')
                    if xa is None:
                        continue
                    href: str = xa.get('href')
                    if not href is None and href != "":
                        detail[f"地址{idx}url"] = href

                    # text
                    alltext = ";".join(xdiv.itertext())
                    if not alltext is None and alltext != "":
                        detail[f"地址{idx}"] = alltext

                    if profile.address is None:
                        profile.address = ""
                    profile.address += "{}\n".format(alltext)

                except Exception as ex:
                    self._logger.debug(
                        "Parse one living_home information failed: {} {} {}".
                        format(profile.nickname, profile.url, ex.args))
                finally:
                    idx += 1

            if len(detail) > 0:
                profile.set_details(**detail)

        except Exception:
            self._logger.error(
                "Parse living_home failed: username:{} url:{}\nerror: {}".
                format(profile._networkid, profile.url,
                       traceback.format_exc()))

###################################
# contact-info 联系信息和基本信息

    def _get_addrinfo(self, profile: NetworkProfile):
        """联系信息"""
        try:
            # education
            # https://www.facebook.com/profile.php?id=100030846743121&sk=about&section=overview&lst=100013325533097%3A100030846743121%3A1568790537

            url: str = "https://www.facebook.com/profile.php?id={}&sk=about&section=contact-info&lst={}%3A{}%3A{}".format(
                profile._userid, self._userid, profile._userid,
                helper_time.ts_since_1970(10))

            html = self._ha.getstring(url,
                                      headers="""
            accept: */*
            accept-encoding: gzip, deflate
            accept-language: en-US,en;q=0.9
            cache-control: no-cache
            content-type: application/x-www-form-urlencoded
            origin: https://www.facebook.com
            pragma: no-cache
            referer: {}
            sec-fetch-mode: cors
            sec-fetch-site: same-origin""".format(profile.url))

            if html is None:
                return

            soup = BeautifulSoup(html.replace('<!--', '').replace('-->', ''), 'lxml')
            # photo
            photo = soup.select_one('._11kf.img')
            if photo:
                try:
                    pic_url = photo.attrs['src'].replace('amp;', '')
                    pic = self._ha.get_response_stream(pic_url)
                    profile._profile_pic = helper_str.base64bytes(pic.read())
                except:
                    pass
            codes = soup.select('.hidden_elem code')
            for code in codes:
                str_code = str(code)
                code = BeautifulSoup(str_code, 'lxml')
                if str_code.__contains__('性别') or str_code.__contains__('出生日期'):
                    sex = re.findall(r'性别.*?class="_2iem">(.*?)</span>', str_code)
                    if sex:
                        profile.gender = sex[0]

                    birth = re.findall(r'出生日期.*?class="_2iem">(.*?)</span>', str_code)
                    if birth:
                        profile.birthday = birth[0]

                elif str_code.__contains__('手机'):
                    try:
                        profile.set_phone(code.select_one('[class="_2iem"]').get_text('--*--').split('--*--')[0]
                                          .replace('.', '').replace('-', '').replace(' ', ''))
                    except:
                        pass
                elif str_code.__contains__('出生日期'):
                    profile.birthday = code.select_one('[class="_2iem"]').get_text()

        except Exception:
            self._logger.error(
                "Get contact-info page failed: username:{} url:{}".format(
                    profile._networkid, profile.url))

    # 失效
    def __parse_contact_info(self, profile: NetworkProfile, ul: str):
        """解析联系信息"""
        try:
            hdoc: etree._Element = etree.XML(ul, etree.XMLParser())
            if hdoc is None:
                self._logger.error(
                    "Parse XML contactinfo failed: {} {}".format(
                        profile.nickname, profile.url))
                return

            xlis = hdoc.findall('li')
            if xlis is None or len(xlis) < 1:
                return

            detail: dict = {}
            idx: int = 0
            for xli in xlis:
                try:
                    xli: etree._Element = xli
                    if xli is None:
                        continue
                    xdiv: etree._Element = xli.find('div')
                    if xdiv is None:
                        continue

                    # key
                    xkey: etree._Element = xdiv.find('div[1]')
                    if xkey is None:
                        continue
                    key: str = ";".join(xkey.itertext())
                    if key is None or key == "":
                        continue

                    # text
                    xval: etree._Element = xdiv.find('div[2]')
                    if xval is None:
                        continue
                    val: str = "".join(xval.itertext())
                    if val is None or val == "":
                        continue

                    detail[key] = val
                    if key.__contains__("Mobile Phones") or key.__contains__(
                            "电话"):
                        profile.set_phone(val)
                    if key.__contains__("Email") or key.__contains__("邮"):
                        profile.set_email(val)

                except Exception as ex:
                    self._logger.debug(
                        "Parse one contactinfo information failed: {} {} {}".
                        format(profile.nickname, profile.url, ex.args))
                finally:
                    idx += 1

            if len(detail) > 0:
                profile.set_details(**detail)

        except Exception:
            self._logger.error(
                "Parse contactinfo failed: username:{} url:{}\nerror: {}".
                format(profile._networkid, profile.url,
                       traceback.format_exc()))

    # 失效
    def __parse_contact_websites(self, profile: NetworkProfile, ul: str):
        """解析工作地"""
        try:
            hdoc: etree._Element = etree.XML(ul, etree.XMLParser())
            if hdoc is None:
                self._logger.error(
                    "Parse XML contact websites failed: {} {}".format(
                        profile.nickname, profile.url))
                return

            xlis = hdoc.findall('li')
            if xlis is None or len(xlis) < 1:
                return

            detail: dict = {}
            for xli in xlis:
                try:
                    xli: etree._Element = xli
                    if xli is None:
                        continue
                    xdiv: etree._Element = xli.find('div')
                    if xdiv is None:
                        continue

                    # key
                    xkey: etree._Element = xdiv.find('div[1]')
                    if xkey is None:
                        continue
                    key: str = ";".join(xkey.itertext())
                    if key is None or key == "":
                        continue

                    xsites: etree._Element = None
                    if key == "Websites":
                        xsites = xdiv.findall('.//li')
                    elif key == "Social Links":
                        xsites = xdiv.findall('div[2]/div/div/span/ul/li')
                    else:
                        xsites = xdiv.findall('.//li')

                    if xsites is None or len(xsites) < 1:
                        continue

                    idx: int = 0
                    for xsite in xsites:
                        try:
                            xsite: etree._Element = xsite
                            val = "".join(xsite.itertext())
                            if val is None or val == "":
                                continue
                            detail[f"{key}{idx}"] = val
                        except Exception:
                            self._logger.debug(
                                "Parse one contact websites information failed: {} {} {}"
                                .format(profile.nickname, profile.url,
                                        ex.args))
                        finally:
                            idx += 1

                except Exception as ex:
                    self._logger.debug(
                        "Parse one contact websites information failed: {} {} {}"
                        .format(profile.nickname, profile.url, ex.args))

            if len(detail) > 0:
                profile.set_details(**detail)

        except Exception:
            self._logger.error(
                "Parse contact websites failed: username:{} url:{}\nerror: {}".
                format(profile._networkid, profile.url,
                       traceback.format_exc()))

###################################
# relationship

    def _get_relation(self, profile: NetworkProfile):
        """家庭关系"""
        try:
            url: str = "https://www.facebook.com/profile.php?id={}&sk=about&section=relationship&lst={}%3A{}%3A{}".format(
                profile._userid, self._userid, profile._userid,
                helper_time.ts_since_1970(10))

            html = self._ha.getstring(url,
                                      headers="""
            accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
            accept-encoding: gzip, deflate
            accept-language: en-US,en;q=0.9
            cache-control: no-cache
            pragma: no-cache
            sec-fetch-mode: navigate
            sec-fetch-site: same-origin
            sec-fetch-user: ?1
            upgrade-insecure-requests: 1
            user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36
            viewport-width: 1600""")

            if html is None:
                return

            m = self._re_info_relation.search(html)
            if m is None:
                self._logger.debug("No relationship info found: {} {}".format(
                    profile.nickname, profile.url))
                return

            strdiv: str = m.group(1).strip()
            m = self._re_relation.search(strdiv)
            if not m is None:
                ul = m.group(1).strip()
                if not ul is None and ul != "":
                    self.__parse_relations(profile, ul)

        except Exception:
            self._logger.error(
                "Get education page failed: username:{} url:{}".format(
                    profile._networkid, profile.url))

    def __parse_relations(self, profile: NetworkProfile, ul: str):
        """家庭关系"""
        try:
            hdoc: etree._Element = etree.XML(ul, etree.XMLParser())
            if hdoc is None:
                self._logger.error(
                    "Parse XML contactinfo failed: {} {}".format(
                        profile.nickname, profile.url))
                return

            xlis = hdoc.findall('li')
            if xlis is None or len(xlis) < 1:
                return

            detail: dict = {}
            idx: int = 0
            for xli in xlis:
                try:
                    xli: etree._Element = xli
                    if xli is None:
                        continue

                    # text
                    text = ",".join(xli.itertext())

                    # url
                    xa = xli.find('div/div/div/div/div/div[2]/div/span/a')
                    if not xa is None:
                        url = xa.get('href')
                        if not url is None and url != "":
                            detail[f"关系{idx}url"] = url

                    detail[f"关系{idx}"] = text

                except Exception as ex:
                    self._logger.debug(
                        "Parse one contactinfo information failed: {} {} {}".
                        format(profile.nickname, profile.url, ex.args))
                finally:
                    idx += 1

            if len(detail) > 0:
                profile.set_details(**detail)

        except Exception:
            self._logger.error(
                "Parse contactinfo failed: username:{} url:{}\nerror: {}".
                format(profile._networkid, profile.url,
                       traceback.format_exc()))

###################################
# bio/detail

    def _get_bio(self, profile: NetworkProfile):
        """住址信息"""
        try:
            # education
            # https://www.facebook.com/profile.php?id=100030846743121&sk=about&section=overview&lst=100013325533097%3A100030846743121%3A1568790537

            url: str = "https://www.facebook.com/profile.php?id={}&sk=about&section=bio&lst={}%3A{}%3A{}".format(
                profile._userid, self._userid, profile._userid,
                helper_time.ts_since_1970(10))

            html = self._ha.getstring(url,
                                      headers="""
            accept: */*
            accept-encoding: gzip, deflate
            accept-language: en-US,en;q=0.9
            cache-control: no-cache
            content-type: application/x-www-form-urlencoded
            origin: https://www.facebook.com
            pragma: no-cache
            referer: {}
            sec-fetch-mode: cors
            sec-fetch-site: same-origin""".format(profile.url))

            if html is None:
                return

            m = self._re_bio_othernames.search(html)
            if not m is None:
                ul = m.group(1).strip()
                self.__parse_bio_othernames(profile, ul)

            m = self._re_bio_favorites.search(html)
            if not m is None:
                ul = m.group(1).strip()
                self.__parse_bio_favorites(profile, ul)

            m = self._re_bio_about.search(html)
            if not m is None:
                ul = m.group(1).strip()
                self.__parse_bio_about(profile, ul)

        except Exception:
            self._logger.error(
                "Get bio page failed: username:{} url:{}".format(
                    profile._networkid, profile.url))

    def __parse_bio_othernames(self, profile: NetworkProfile, ul: str):
        """详情othernames"""
        try:
            hdoc: etree._Element = etree.XML(ul, etree.XMLParser())
            if hdoc is None:
                self._logger.error(
                    "Parse XML bio othernames failed: {} {}".format(
                        profile.nickname, profile.url))
                return

            xkey = hdoc.find('div/span')
            if xkey is None:
                return
            key = ",".join(xkey.itertext())
            if key is None or key == "":
                return

            xlis = hdoc.findall('ul/li')
            if xlis is None or len(xlis) < 1:
                return

            detail: dict = {}
            idx: int = 0
            for xli in xlis:
                try:
                    xli: etree._Element = xli
                    text = ",".join(xli.itertext())
                    if text is None or text == "":
                        continue
                    detail[f'{key}{idx}'] = text

                except Exception as ex:
                    self._logger.debug(
                        "Parse one bio othernames failed: {} {} {}".format(
                            profile.nickname, profile.url, ex.args))
                finally:
                    idx += 1

            if len(detail) > 0:
                profile.set_details(**detail)

        except Exception:
            self._logger.error(
                "Parse bio othernames failed: username:{} url:{}\nerror: {}".
                format(profile._networkid, profile.url,
                       traceback.format_exc()))

    def __parse_bio_favorites(self, profile: NetworkProfile, ul: str):
        """详情 favorites"""
        try:
            hdoc: etree._Element = etree.XML(ul, etree.XMLParser())
            if hdoc is None:
                self._logger.error(
                    "Parse XML bio favorites failed: {} {}".format(
                        profile.nickname, profile.url))
                return

            xkey = hdoc.find('div/span')
            if xkey is None:
                return
            key = ",".join(xkey.itertext())
            if key is None or key == "":
                return

            xlis = hdoc.findall('ul/li')
            if xlis is None or len(xlis) < 1:
                return

            detail: dict = {}
            idx: int = 0
            for xli in xlis:
                try:
                    xli: etree._Element = xli
                    text = " ".join(xli.itertext())
                    if text is None or text == "":
                        continue
                    detail[f'{key}{idx}'] = text

                except Exception as ex:
                    self._logger.debug(
                        "Parse one bio othernames failed: {} {} {}".format(
                            profile.nickname, profile.url, ex.args))
                finally:
                    idx += 1

            if len(detail) > 0:
                profile.set_details(**detail)

        except Exception:
            self._logger.error(
                "Parse contactinfo failed: username:{} url:{}\nerror: {}".
                format(profile._networkid, profile.url,
                       traceback.format_exc()))

    def __parse_bio_about(self, profile: NetworkProfile, ul: str):
        """详情 about"""
        try:
            hdoc: etree._Element = etree.XML(ul, etree.XMLParser())
            if hdoc is None:
                self._logger.error(
                    "Parse XML contactinfo failed: {} {}".format(
                        profile.nickname, profile.url))
                return

            xkey = hdoc.find('div/span')
            if xkey is None:
                return
            key = ",".join(xkey.itertext())
            if key is None or key == "":
                return

            xlis = hdoc.findall('ul/li')
            if xlis is None or len(xlis) < 1:
                return

            detail: dict = {}
            idx: int = 0
            for xli in xlis:
                try:
                    xli: etree._Element = xli
                    text = " ".join(xli.itertext())
                    if text is None or text == "":
                        continue
                    detail[f'{key}{idx}'] = text

                except Exception as ex:
                    self._logger.debug(
                        "Parse one bio othernames failed: {} {} {}".format(
                            profile.nickname, profile.url, ex.args))
                finally:
                    idx += 1

            if len(detail) > 0:
                profile.set_details(**detail)

        except Exception:
            self._logger.error(
                "Parse contactinfo failed: username:{} url:{}\nerror: {}".
                format(profile._networkid, profile.url,
                       traceback.format_exc()))


###################################
# year-overviews

    def _get_overview(self, profile: NetworkProfile):
        """住址信息"""
        try:
            # education
            # https://www.facebook.com/profile.php?id=100030846743121&sk=about&section=overview&lst=100013325533097%3A100030846743121%3A1568790537

            url: str = "https://www.facebook.com/profile.php?id={}&sk=about&section=year-overviews&lst={}%3A{}%3A{}".format(
                profile._userid, self._userid, profile._userid,
                helper_time.ts_since_1970(10))

            html = self._ha.getstring(url,
                                      headers="""
            accept: */*
            accept-encoding: gzip, deflate
            accept-language: en-US,en;q=0.9
            cache-control: no-cache
            content-type: application/x-www-form-urlencoded
            origin: https://www.facebook.com
            pragma: no-cache
            referer: {}
            sec-fetch-mode: cors
            sec-fetch-site: same-origin""".format(profile.url))

            if html is None:
                return

            m = self._re_info.search(html)
            if m is None:
                self._logger.debug(
                    "No year-overviews info found: {} {}".format(
                        profile.nickname, profile.url))
                return

            strdiv: str = m.group(1).strip()

            print(strdiv)

        except Exception:
            self._logger.error(
                "Get year-overviews page failed: username:{} url:{}".format(
                    profile._networkid, profile.url))
