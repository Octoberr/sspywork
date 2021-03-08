import re
import threading
import traceback
from io import BytesIO
from sys import platform

from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.common.exceptions import TimeoutException, WebDriverException

from datacontract.iscoutdataset import IscoutTask
from idownclient.config_spiders import (webdriver_path_debian,
                                        webdriver_path_win)
from .scoutplugbase import ScoutPlugBase
from ...clientdatafeedback.scoutdatafeedback import Email, Phone, ScreenshotUrl


class UrlInfo(ScoutPlugBase):
    """暂时 单例单线程，同时只能有一个页面在加载"""

    # _driver_started: bool = False
    # _driver_locker = threading.RLock()
    #
    # _driver: webdriver.Chrome = None
    #
    # _run_locker = threading.RLock()
    #
    # _logger: MsLogger = MsLogManager.get_logger("Urlinfo")

    def __init__(self, task: IscoutTask):
        ScoutPlugBase.__init__(self)
        self.task = task
        self._re_title = re.compile(r'<title>(.*?)</title>', re.S | re.M)
        # <meta content="17173,17173.com,17173游戏网,网络游戏" name="Keywords" />
        self._re_meta = re.compile(
            r'<meta[^>]+?name="(keywords|description)"[^>]+?/>',
            re.S | re.M | re.IGNORECASE)
        self._run_locker = threading.RLock()
        self._driver: webdriver.Chrome = self._start_driver()
        if self._driver is None:
            raise Exception("Init chrome driver error, try again")

    # @classmethod
    # def _start_driver(cls):
    #     try:
    #         if platform == 'linux' or platform == 'linux2':
    #             driver_path = webdriver_path_debian
    #         elif platform == 'win32':
    #             driver_path = webdriver_path_win
    #         chrome_options = ChromeOptions()
    #         chrome_options.add_argument('--headless')
    #         chrome_options.add_argument('--no-sandbox')
    #         chrome_options.add_argument('log-level=3')
    #         # info(default) = 0
    #         # warning = 1
    #         # LOG_ERROR = 2
    #         # LOG_FATAL = 3
    #         cls._driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=driver_path)
    #         cls._driver.set_page_load_timeout(30)
    #         cls._driver.set_script_timeout(30)
    #         cls._driver.implicitly_wait(30)
    #         cls._driver_started = True
    #
    #     except Exception:
    #         cls._logger.error(traceback.format_exc())

    def _start_driver(self):
        driver = None
        try:
            # if platform == 'linux' or platform == 'linux2':
            driver_path = webdriver_path_debian
            # elif platform == 'win32':
            #     driver_path = webdriver_path_win
            chrome_options = ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument("--window-size=1440,900")
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('lang=zh_CN.UTF-8')
            chrome_options.add_argument('log-level=3')
            driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=driver_path)
            # 因为加载了浏览器，所以设置等待时间长一点避免崩溃
            driver.set_page_load_timeout(30)
            driver.set_script_timeout(60)
            driver.implicitly_wait(30)
        except Exception:
            self._logger.error(traceback.format_exc())
        return driver

    def _make_phone(self, html, level, reason=None):
        """
        提取html source中的手机号
        ^\d{3,4}-?\d{7,8}$|13[0-9]{9}
        这个只能满足大部分情况，涵盖不了所有的手机号种类

        modify by judy
        后期想做成去匹配每个国家
        :param html:
        :param level:
        :param reason:
        :return:
        """
        re_phone = re.compile(r'^\d{3,4}\-?\d{7,8}$|13[0-9]{9}')
        try:
            for m in re_phone.finditer(html):
                mphone = m.group(0)

                if isinstance(mphone, str) and mphone != '':
                    if not mphone.startswith('+'):
                        phone = '+' + mphone
                    else:
                        phone = mphone
                    p = Phone(self.task, level, phone)
                    p.reason = reason
                    p.source = reason
                    yield p
        except TimeoutError:
            pass
        except Exception:
            self._logger.error("Match phone error: {}".format(
                traceback.format_exc()))

    def _make_email(self, html, level, reason=None):
        """
        提取html source中的邮箱账号
        [\w-\.]+@([\w-]+\.)+[a-z]{2,3}
        这个也只能涵盖主流的邮箱账号，无法匹配所有
        :param html:
        :param level:
        :param reason:
        :return:
        """
        try:
            re_email = re.compile(r'[\w.-]+@[\w.-]+\.+[a-z]{2,3}')
            # emails = re_email.findall(html, timeout=2) # 据说py3支持timeout参数，然而并没有？
            for m in re_email.finditer(html):
                email = m.group(0)
                e = Email(self.task, level, email)
                e.reason = reason
                e.source = reason
                yield e
        except TimeoutError:
            pass
        except Exception:
            self._logger.error("Match email error: {}".format(
                traceback.format_exc()))

    def visit_url(self, url, level, reason=None):
        try:
            # if not UrlInfo._driver_started:
            #     with UrlInfo._driver_locker:
            #         if not UrlInfo._driver_started:
            #             self._start_driver()
            # 因为一些原因导致了webdrivercrash了手动关闭再打开 by judy 20201031
            if self._driver is None:
                self._driver = self._start_driver()

            with self._run_locker:
                # url: str = obj.value
                # driver = self._start_driver()
                # 加载一个浏览器
                self._driver.get(url)
                self._driver.maximize_window()
                self._logger.debug(f"Visit {url} successed")
                pagesource = self._driver.page_source
                self._logger.debug(f"Get {url} homepage source code")
                yield (pagesource, 'homecode')
                # 根据pagesource去提取email和phone
                if pagesource is not None or pagesource != '':
                    # phone
                    # 有些url中有很多图片，会导致正则表达式卡死，所以可以优先将图片删除
                    source_del_pic = re.sub(r';base64,.+?=', '', pagesource)

                    for phone in self._make_phone(source_del_pic, level, reason):
                        yield (phone, 'phone')
                    # email
                    for email in self._make_email(source_del_pic, level, reason):
                        yield (email, 'email')

                # meta，title
                titles = self._re_title.findall(pagesource)
                if titles:
                    title = titles[0]
                else:
                    title = None
                metas = self._re_meta.findall(pagesource)
                if metas:
                    meta = metas[0]
                else:
                    meta = None
                if title is not None:
                    self._logger.debug(f"Get {url} title")
                    yield (title, meta, 'summary')

                # 截图 self._driver.current_url 百度的url会有些许差别，使用确认的url
                src = ScreenshotUrl(self.task, level, self.task._object, self.task._objecttype, url)
                screen_png = self._driver.get_screenshot_as_png()
                stream = BytesIO(screen_png)
                self._logger.debug(f"Get {url} screenshot")
                src.stream = stream
                yield (src, 'screenshot')

        except TimeoutException:
            self._logger.info(f"Visit {url} timeout, try another url")
        except WebDriverException:
            self._logger.info(f"Web driver may be crash, need another page\nerr{traceback.format_exc()}")
            # 先关后开,在程序执行的时候统一再开
            if self._driver is not None:
                self._driver.close()
            # self._driver = self._start_driver()

        except Exception:
            self._logger.error('Visit url fail! URL:{}\nerr:{}'.format(url, traceback.format_exc()))
            # 报错了就把这个关了
            if self._driver is not None:
                self._driver.close()
            # self._driver = self._start_driver()

    def __del__(self):
        """
        删除下这个driver
        :return:
        """
        if self._driver is not None:
            self._driver.close()
