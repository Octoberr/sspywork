"""
这里使用的npm安装的webappalyzer
这样使用不仅免费而且快、结果全
create by judy 2019/08/05

wappalyzer在64位linux的机器上使用chrome插件会造成cpu超频500%，同时还会残留大量的僵尸线程
修改调用方式
modify by judy 2021/02/02
"""
import re
import traceback
from Wappalyzer import Wappalyzer, WebPage

from commonbaby.httpaccess import HttpAccess
from commonbaby.mslog import MsLogger, MsLogManager

from idownclient.clientdatafeedback.scoutdatafeedback import Component
from .cmsfinger import cmsver


class WebAlyzer(object):
    def __init__(self, task):
        self.task = task
        self._logger: MsLogger = MsLogManager.get_logger("webalyzer")

        self._cmsver_lower = {}
        for k, v in cmsver.items():
            self._cmsver_lower[k.lower()] = v

    def __parse_alyzer_res(self, res: dict):
        """
        解析拿到的结果，
        :param res: json data
        :return:
        """
        ...

    #         """
    #         {
    #   "Font Awesome": {
    #     "categories": [
    #       "Font scripts"
    #     ],
    #     "versions": [
    #       "5.4.2"
    #     ]
    #   },
    #   "Google Font API": {
    #     "categories": [
    #       "Font scripts"
    #     ],
    #     "versions": []
    #   },
    #   "MySQL": {
    #     "categories": [
    #       "Databases"
    #     ],
    #     "versions": []
    #   },
    #   "Nginx": {
    #     "categories": [
    #       "Web servers",
    #       "Reverse proxies"
    #     ],
    #     "versions": []
    #   },
    #   "PHP": {
    #     "categories": [
    #       "Programming languages"
    #     ],
    #     "versions": [
    #       "5.6.40"
    #     ]
    #   },
    #   "WordPress": {
    #     "categories": [
    #       "CMS",
    #       "Blogs"
    #     ],
    #     "versions": [
    #       "5.4.2"
    #     ]
    #   },
    #   "Yoast SEO": {
    #     "categories": [
    #       "SEO"
    #     ],
    #     "versions": [
    #       "14.6.1"
    #     ]
    #   }
    # }
    #         """

    def get_alyzer_res(self, level, url: str):
        """
        这里去获取结果
        :param level:
        :param url:
        :return:
        """
        # 为url添加头
        target = url
        if not (url.startswith("https://") or url.startswith("http://")):
            target = "http://" + url
        # -w是ms单位，即超过那个时间后就不再继续搞了
        try:
            # 只初始化一个wappalyzer
            wappalyzer = Wappalyzer.latest()
            webpage = WebPage.new_from_url(target, verify=False)
            info = wappalyzer.analyze_with_versions_and_categories(webpage)
            if not isinstance(info, dict) or info.__len__() <= 0:
                return

            for k, v in info.items():
                name = k
                versions = v.get("versions", [])
                categories = v.get("categories", [])
                if name is None or name == "":
                    continue
                for i in range(len(categories)):
                    ctname = categories[i]
                    if ctname.lower() == "cms":
                        self._logger.debug("Start CMS ver detection: {}".format(target))
                        ver = self._recognize_cms_ver(target, name)
                        if ver is not None:
                            version = ver
                            self._logger.debug(
                                "Got cms version: {}:{}".format(name, version)
                            )

                    com = Component(self.task, level, name)
                    com.category = ctname
                    com.url = target
                    if len(versions) >= i + 1:
                        com.ver = versions[i]
                    yield com
        except Exception as errs:
            self._logger.error(f"Wappaylyzer found nothing\nerr:{errs}")

    def _recognize_cms_ver(self, host: str, name: str) -> str:
        """recognize cms and version"""
        ver: str = None
        try:
            if not self._cmsver_lower.__contains__(name.lower()):
                return ver

            path, rgx = self._cmsver_lower[name.lower()]

            ver: str = self._get_cms_ver(host, path, rgx)

        except Exception:
            self._logger.error(
                "Recognize cms err: host={} name={} err={}".format(
                    host, name, traceback.format_exc()
                )
            )
        return ver

    def _get_cms_ver(self, host: str, path: str, rgx: re.Pattern):
        ver: str = None
        try:
            ha = HttpAccess()
            # access home page to get cookie
            url = host
            if not url.startswith("http"):
                url = "http://" + host.strip("/")
            self._logger.debug("Get CMS ver home: {}".format(url))
            ha.getstring(
                url,
                headers="""
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
            Accept-Encoding: gzip, deflate
            Accept-Language: en-US,en;q=0.9
            Cache-Control: no-cache
            Pragma: no-cache
            Proxy-Connection: keep-alive
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36""",
                timeout=10,
            )

            # access version page
            url = host.strip("/") + "/" + path.lstrip("/")
            if not url.startswith("http"):
                url = "http://" + host.strip("/") + "/" + path.lstrip("/")
            self._logger.debug("Get CMS ver subpath: {}".format(url))
            html = ha.getstring(
                url,
                headers="""
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
            Accept-Encoding: gzip, deflate
            Accept-Language: en-US,en;q=0.9
            Cache-Control: no-cache
            Pragma: no-cache
            Proxy-Connection: keep-alive
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36""",
                timeout=10,
            )

            if html is None or html == "":
                return ver

            # <version>(.+)</version>
            m: re.Match = re.search(rgx, html, re.S)
            if m is None:
                return ver

            ver = m.group(1)

        except Exception as e:
            self._logger.error("Get joomla version faile: {} {}".format(host, e.args))
        return ver
