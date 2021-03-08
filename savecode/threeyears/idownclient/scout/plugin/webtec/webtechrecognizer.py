"""web technology recognizer"""

# -*- coding:utf-8 -*-

import json
import re
import threading
import time
import traceback
from pathlib import Path
from datetime import datetime
import pytz

import requests
from commonbaby.httpaccess import HttpAccess, ResponseIO

from datacontract.iscoutdataset import IscoutTask
from idownclient.clientdatafeedback.scoutdatafeedback import Component
from idownclient.scout.plugin.scoutplugbase import ScoutPlugBase


# https://raw.githubusercontent.com/AliasIO/Wappalyzer/master/src/apps.json
# https://www.wappalyzer.com/
# app.json fields meaning:
# https://www.wappalyzer.com/docs/specification

class WebTech(object):
    """represents a web tech"""

    __cats: dict = {}
    __cats_set_locker = threading.RLock()

    def __init__(self, name: str, source: dict):
        if not isinstance(name, str) or name == "":
            raise Exception("Invalid WebTech name")
        self._name: str = name
        self._source: str = source

        self._cats: list = source.get("cats", [])
        self._icon: str = source.get("icon")
        self._website: str = source.get("website")
        self._url: str = source.get("url")

        self._implies: list = source.get("implies")
        if isinstance(self._implies, str) and self._implies is not None:
            self._implies = [self._implies]
        self._excludes: list = source.get("excludes")
        if isinstance(self._excludes, str):
            self._excludes = [self._excludes]

        self._cookies: dict = source.get("cookies", {})
        self._js: dict = source.get("js", {})
        self._headers: dict = source.get("headers", {})
        self._html: str = source.get("html", None)
        self._meta: dict = source.get("meta", {})
        self._script: str = source.get("script", None)

    @classmethod
    def set_cats(cls, key: str, catname: str):
        with WebTech.__cats_set_locker:
            WebTech.__cats[key] = catname

    @classmethod
    def get_cat_name(cls, cat: str):
        """
        根据传入的cat找到对应的组件名字
        :param cat:
        :return:
        """
        if not isinstance(cat, str):
            cat = str(cat)
        return cls.__cats.get(cat)


class WebTechRecognizer(ScoutPlugBase):
    """Recognizer for web technologies"""

    __inst = None
    __initialed: bool = False
    __initlocker = threading.RLock()
    # 文件夹
    file = Path(__file__).parents[0]

    # __appfi = os.path.abspath(os.path.join("./resource/tools/apps.json"))
    __appfi: Path = file / 'apps.json'
    __ha: HttpAccess = HttpAccess()
    _webtechs: dict = {}

    def __init__(self, task: IscoutTask):
        ScoutPlugBase.__init__(self)
        self.task = task
        self.__init()

    def __init(self):
        """check if the resource apps.json is exists, 
        otherwise download it."""
        if WebTechRecognizer.__initialed:
            return
        with WebTechRecognizer.__initlocker:
            if WebTechRecognizer.__initialed:
                return

            # 如果没有文件那么去下载
            if not WebTechRecognizer.__appfi.exists():
                self.__download_appfi()
            # 如果有文件那么去检查下更新，超过7天重新下载
            self.__update_appfi()
            # 初始化json文件，将文件加载到内存
            if not self.__init_json():
                raise Exception("Init web_tech_recognizer json failed.")

            WebTechRecognizer.__initialed = True

    def __download_appfi(self):
        """download app.json"""
        url: str = 'https://raw.githubusercontent.com/AliasIO/Wappalyzer/master/src/apps.json'
        respio: ResponseIO = WebTechRecognizer.__ha.get_response_stream(url)
        with WebTechRecognizer.__appfi.open(mode='wb') as fs:
            respio.readinto(fs)

    def __update_appfi(self):
        """
        如果存在文件，那么检查下文件是否超过7天，
        如果超过7天那么删除重新下载
        直接使用unixtime
        :return:
        """
        file_time = int(WebTechRecognizer.__appfi.stat().st_mtime)
        now_time = int(datetime.now(pytz.timezone('Asia/Shanghai')).timestamp())
        if now_time - file_time > 7 * 24 * 60 * 60:
            # 先删除文件
            WebTechRecognizer.__appfi.unlink()
            # 重新下载
            self.__download_appfi()

    def __init_json(self) -> bool:
        """init app.json"""
        sj = None
        with open(WebTechRecognizer.__appfi, mode='r', encoding='utf-8') as fs:
            sj = json.load(fs)

        if not sj.__contains__("apps"):
            raise Exception('Key "apps" not found in app.json')
        if not sj.__contains__("categories"):
            raise Exception('Key "categories" not found in app.json')

        for c, v in sj["categories"].items():
            WebTech.set_cats(c, v["name"])

        for name, source in sj["apps"].items():
            webtec: WebTech = WebTech(name, source)
            WebTechRecognizer._webtechs[name] = webtec

        return True

    #######################################
    # match
    def __judge_two_str(self, sstr, dstr):
        """
        判断两个字符串，是否类似
        :param sstr:
        :param dstr:
        :return:
        """
        res = False
        if sstr in dstr or dstr in sstr or sstr == dstr:
            res = True
        return res

    def __url_match(self, url: str):
        """
        根据url来匹配组件，先之前已经做了很多判断所以这个url是能拿到的
        目前好像只能通过一次循环来查找,
        这个json里面的url好像是这个组件的url
        :param url:
        :return:
        """
        try:
            for k, v in WebTechRecognizer._webtechs.items():
                webtech: WebTech = v
                if webtech._url is not None and self.__judge_two_str(url, webtech._url):
                    for cat in webtech._cats:
                        name = WebTech.get_cat_name(cat)
                        if name is not None:
                            self._logger.debug(f"Url match a component,name:{name}")
                            yield name
                    # 目前都只去匹配一次，因为情况比较特殊，所以先这么干
                    break
        except:
            self._logger.error(f"Url match error, err:{traceback.format_exc()}")
        finally:
            self._logger.info("Complete use url to match component.")

    def __rheader_match(self, rheader: dict):
        """
        根据返回的header来匹配
        :param rheader:
        :return:
        """
        try:
            get = False
            for k, v in WebTechRecognizer._webtechs.items():
                webtech: WebTech = v
                # 如果发现指纹库里的header不为空，那么就去对比下
                if len(webtech._headers) != 0:
                    # 遍历传入的header去对比
                    for sk, sv in rheader.items():
                        # 判断信息是否符合
                        if webtech._headers.__contains__(sk):
                            # 这里的正则好像都有version，但是实际上得到的值可能没有，所以需要判断下
                            match = False
                            wh = webtech._headers[sk]
                            if 'version' in sv:
                                re_header = re.compile(wh)
                                match = re_header.search(sv)
                            else:
                                # 这里有两种情况'.+?\;version:\d+'
                                if 'version' in wh:
                                    try:
                                        re_header = re.compile(wh.split('version')[0][:-2])
                                    except:
                                        self._logger.debug(f'Cant split version, server:{wh}')
                                else:
                                    re_header = re.compile(wh)
                                match = re_header.search(sv)
                            if match:
                                self._logger.debug(f"Header match component, name:{k}")
                                for cat in webtech._cats:
                                    category = WebTech.get_cat_name(cat)
                                    if category is not None:
                                        self._logger.info(f"Rheader match a component,name:{category}")
                                        yield (k, v, category)
                                get = True
                                break
                # 如果遍历到了数据了那么就不再需要继续拿了，一个网站应该不会使用那么技术
                # 如果以后需要那么多的数据那么就把这个去掉继续拿
                if get:
                    break
        except:
            self._logger.error(f"Rheader match error, err:{traceback.format_exc()}")
        finally:
            self._logger.info("Complete use rheader to match component.")

    def __html_match(self, html: str):
        """
        根据返回的html来匹配
        :param html:
        :return:
        """
        try:
            for k, v in WebTechRecognizer._webtechs.items():
                webtech: WebTech = v
                if webtech._html is not None:
                    # html只有一个，直接就是正则表达式
                    match = False
                    if isinstance(webtech._html, str):
                        re_html = re.compile(webtech._html)
                        match = re_html.search(html)
                    else:
                        # html有多个，有多个正则表达式
                        for he in webtech._html:
                            re_html = re.compile(he)
                            match = re_html.search(html)
                            if match:
                                break
                    if match:
                        self._logger.debug(f"Html match component, name:{k}")
                        for cat in webtech._cats:
                            category = WebTech.get_cat_name(cat)
                            if category is not None:
                                self._logger.info(f"Html match a component, name:{category}")
                                yield (k, v, category)
                        # 目前就只去匹配一次
                        break
        except:
            self._logger.error(f"Html match error, err:{traceback.format_exc()}")
        finally:
            self._logger.info("Complete use html to match component.")

    def _match(self, url: str, respheader: dict, html: str):
        """
        根据传入的数据匹配相应的组件
        return (name, category, version)
        :param url:
        :param respheader:
        :param html:
        :return:
        """
        # 这里进行很多判断确保条件不会出错，然后去拿相应的数据
        # 目前在这只能拿到组件的英文名字，所以直接将数据返回，然后在上一层封装成
        # if url is not None and url != '':
        #     for data in self.__url_match(url):
        #         yield data
        self._logger.info(f"Start to find component, url:{url}")
        if respheader is not None and len(respheader) > 0:
            for data in self.__rheader_match(respheader):
                yield data
        if html is not None and html != '':
            for data in self.__html_match(html):
                yield data

    def get_match_res(self, level, url):
        """
        根据url和
        :param level:
        :param url:
        :return:
        """
        try:
            res = requests.get(url)
            # url = res.url
            rheaders = dict(res.headers)
            html = res.text
            match_iter = self._match(url, rheaders, html)
            for k, v, categroy in match_iter:
                com = Component(self.task, level, k)
                com.category = categroy
                com.url = v._website
                yield com
        except:
            self._logger.error(f"Match component error, err:{traceback.format_exc()}")
