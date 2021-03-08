"""
url scouter
2019/07/10
"""
import traceback
from urllib import parse

from datacontract import EObjectType, IscoutTask
from idownclient.clientdatafeedback.scoutdatafeedback import URL, Component
from outputmanagement import OutputManagement
from .scouterbase import ScouterBase, ScoutFeedBackBase
from ..plugin import UrlInfo, WafDetect, WebAlyzer


class ScouterUrl(ScouterBase):
    """"""

    TARGET_OBJ_TYPE = EObjectType.Url

    def __init__(self, task: IscoutTask):
        ScouterBase.__init__(self, task)

    def __segment_output(self, root: URL, level, url) -> URL:
        """
        分段输出数据，达到分段输出的标准后给新的root
        没有达到那么就给旧的root
        :param root:
        :return:
        """
        # 加载到max output就输出
        # 如果输出了那么就返回新的根节点
        if root._subitem_count() >= self.max_output:
            self.outputdata(root.get_outputdict(), root._suffix)
            root: URL = URL(self.task, level, url)
        return root

    def __output_getdata(self, root: URL, level, url: str) -> URL:
        """
        单个插件拿到的数据太大了，每个插件执行完成后都输出下
        :param root:
        :param level:
        :param url:
        :return:
        """
        if root._subitem_count() > 0:
            self.outputdata(root.get_outputdict(), root._suffix)
            root: URL = URL(self.task, level, url)
        return root

    def __set_value(self, root: URL, data):
        """
        插入数据
        :param root:
        :param data:
        :return:
        """
        if isinstance(data, Component):
            root.set_component(data)

    def _scoutsub(self, level, obj: ScoutFeedBackBase) -> iter:
        """
        名字到时候用的时候再改
        :return:
        """
        root: URL = URL(self.task, level, obj.value)
        try:
            # 使用组件
            for cpd in self._get_component(
                root, self.task, level, obj, reason=self.dtools.urlInfo
            ):
                yield cpd
            root = self.__output_getdata(root, level, url=obj.value)

            # ---------------------------------------新增
            # 首页源码，内容摘要，首页截图这3个东西应该是能在一个方法里获取的，如果不能，那么自行拆分
            for data in self._get_home_info(
                root, self.task, level, obj, reason=self.dtools.urlInfo
            ):
                yield data
            root = self.__output_getdata(root, level, url=obj.value)

            # waf_detect
            for data in self._get_waf_detect(
                root, self.task, level, obj, reason=self.dtools.waf_detect
            ):
                yield data
            root = self.__output_getdata(root, level, url=obj.value)

        except:
            self._logger.error(f"Scouter url error, err:{traceback.format_exc()}")
        finally:
            # 最后结束完成也要输出
            if root._subitem_count() > 0:
                self.outputdata(root.get_outputdict(), root._suffix)

    # ---------------------------------- component
    def _get_component(
        self, root: URL, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ):
        """
        获取url的component
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """
        if not task.cmd.stratagyscout.cmdurl.enabled_components:
            return

        self._logger.debug("URL:Start getting component.")

        url: str = obj.value
        log = f"开始收集目标{url}组件信息"
        self._outprglog(log)
        count = 0
        try:
            for comd in self.__wappalyzer(root, task, level, url):
                count += 1
                yield comd
        except:
            self._logger.error(f"Get wappalyzer error, err:{traceback.format_exc()}")
        finally:
            log = f"获取到目标{url}未经处理的{count}条{self.dtools.urlInfo}数据"
            self._outprglog(log)

    def __wappalyzer(self, root: URL, task: IscoutTask, level, url):
        """
        wappalyzer网站获取url的组件
        :param root:
        :param task:
        :param level:
        :param url:
        :return:
        """
        try:
            wap = WebAlyzer(task)
            for component in wap.get_alyzer_res(level, url):
                self.__set_value(root, component)
                root = self.__segment_output(root, level, url)
                yield component
        except:
            self._logger.error(
                f"Wappalyzer get component error, err:{traceback.format_exc()}"
            )

    def _get_home_info(
        self, root: URL, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ):
        """
        这个方法用来获取首页的信息，如果不能在一个方法内获取完成，那么就再拆分
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """
        # task.cmd.stratagyscout.cmdurl.enabled_homepage_code
        # task.cmd.stratagyscout.cmdurl.enabled_summary
        # task.cmd.stratagyscout.cmdurl.enabled_homepage_screenshot
        self._logger.debug("URL:Start getting homeinfo.")
        url: str = obj.value
        log = f"开始收集目标{url}的{self.dtools.urlInfo}相关信息"
        self._outprglog(log)
        # 一个方法可以将3个东西获取完成
        count = 0
        u_info = None
        try:
            u_info = UrlInfo(task)
            for data in u_info.visit_url(url, level, reason):
                if data is None:
                    continue
                data_type = data[-1]
                try:
                    # home page code
                    if (
                        data_type == "homecode"
                        and task.cmd.stratagyscout.cmdurl.enabled_homepage_code
                    ):
                        root.set_homepage_code(data[0])
                        count += 1
                    # title meta
                    elif (
                        data_type == "summary"
                        and task.cmd.stratagyscout.cmdurl.enabled_summary
                    ):
                        root.set_homepage_summary(data[0], data[1])
                        count += 1
                    # screen shot
                    elif (
                        data_type == "screenshot"
                        and task.cmd.stratagyscout.cmdurl.enabled_homepage_screenshot
                    ):
                        # 这个数据是直接输出的
                        OutputManagement.output(data[0])
                        count += 1
                    yield data
                    task.success_count()
                except:
                    task.fail_count()
                    self._logger.error(
                        f"Set data error,datatype:{data_type}, error:{traceback.format_exc()}"
                    )
                    continue
        except:
            self._logger.error(f"Get homeinfo error, err:{traceback.format_exc()}")
        finally:
            log = f"获取到目标{url}未经处理的{count}条{self.dtools.urlInfo}数据"
            self._outprglog(log)
            # 手动关闭下浏览器
            if u_info is not None:
                del u_info

    # ------------------------------------waf_detect目标防护探测
    def _get_waf_detect(
        self, root: URL, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ):
        """
        目标防护探测，探测web应用防火墙指纹，识别WAF类型
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """
        if not task.cmd.stratagyscout.cmdurl.enabled_waf_detect:
            return

        self._logger.debug("URL: Start getting waf_detect info.")

        domain: str = obj.value
        log = f"开始收集目标{domain} {self.dtools.waf_detect}信息"
        self._outprglog(log)
        count_dict = {}
        try:
            if domain.startswith("http"):
                url = parse.urlparse(domain)
                domain = url.netloc

            wd = WafDetect(task)
            if "http://" in domain or "https://" in domain:
                self._logger.error("http:// or https:// should not in domain!")
                return
            # 探测目标是HTTP协议
            for waf in wd.waf_detect("http://" + domain):
                if not isinstance(waf, str):
                    continue
                root.set_waf(waf)
                count_dict[waf] = 1
                root = self.__segment_output(root, level, obj.value)
                yield waf
            task.success_count()
            # 探测目标是HTTPS协议
            for waf in wd.waf_detect("https://" + domain):
                if not isinstance(waf, str):
                    continue
                root.set_waf(waf)
                count_dict[waf] = 1
                root = self.__segment_output(root, level, obj.value)
                yield waf
            task.success_count()
        except Exception:
            task.fail_count()
            self._logger.error(
                "Waf detect error:\ntaskid:{}\nbatchid:{}\nobj:{}\nerror:{}".format(
                    self.task.taskid,
                    self.task.batchid,
                    obj.value,
                    traceback.format_exc(),
                )
            )
        finally:
            log = f"获取到目标{domain}未经处理的{count_dict.__len__()}条{self.dtools.waf_detect}数据"
            self._outprglog(log)
