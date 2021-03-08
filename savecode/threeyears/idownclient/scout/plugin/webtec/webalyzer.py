"""
这里使用的npm安装的webappalyzer
这样使用不仅免费而且快结果全
create by judy 2019/08/05
"""
from subprocess import Popen, PIPE
import json
from datacontract.iscoutdataset import IscoutTask
from idownclient.clientdatafeedback.scoutdatafeedback import Component
from idownclient.scout.plugin.scoutplugbase import ScoutPlugBase
import traceback


class WebAlyzer(ScoutPlugBase):

    def __init__(self, task):
        ScoutPlugBase.__init__(self)
        self.task: IscoutTask = task

    def __parse_alyzer_res(self, res: str):
        """
        解析拿到的结果，
        :param res: json data
        :return:
        """
        data = json.loads(res)
        self._logger.debug(res)
        app = data.get('technologies', [])
        if len(app) > 0:
            for appinfo in app:
                categorys = appinfo.get('categories')
                if isinstance(categorys, list):
                    for category in categorys:
                        yield (category, appinfo.get('name'), appinfo.get('website'), appinfo.get('version'))
                elif isinstance(categorys, dict):
                    yield (categorys, appinfo.get('name'), appinfo.get('website'), appinfo.get('version'))

    def get_alyzer_res(self, level, url: str):
        """
        这里去获取结果
        :param level:
        :param url:
        :return:
        """
        # 为url添加头
        if not (url.startswith('https://') or url.startswith('http://')):
            url = 'http://' + url
        try:
            proc = Popen(f'wappalyzer {url}', stdout=PIPE, shell=True)
            outs, errs = proc.communicate(timeout=60)
            res = outs.decode('utf-8')
            #             res = '''
            #             [
            #     {
            #         "slug": "wordpress",
            #         "name": "WordPress",
            #         "confidence": 100,
            #         "version": null,
            #         "icon": "WordPress.svg",
            #         "website": "https://wordpress.org",
            #         "cpe": "cpe:/a:wordpress:wordpress",
            #         "categories": [
            #             {
            #                 "id": 1,
            #                 "slug": "cms",
            #                 "name": "CMS"
            #             },
            #             {
            #                 "id": 11,
            #                 "slug": "blogs",
            #                 "name": "Blogs"
            #             }
            #         ]
            #     },
            #     {
            #         "slug": "mysql",
            #         "name": "MySQL",
            #         "confidence": 100,
            #         "version": null,
            #         "icon": "MySQL.svg",
            #         "website": "http://mysql.com",
            #         "cpe": "cpe:/a:mysql:mysql",
            #         "categories": [
            #             {
            #                 "id": 34,
            #                 "slug": "databases",
            #                 "name": "Databases"
            #             }
            #         ]
            #     },
            #     {
            #         "slug": "php",
            #         "name": "PHP",
            #         "confidence": 100,
            #         "version": null,
            #         "icon": "PHP.svg",
            #         "website": "http://php.net",
            #         "cpe": "cpe:/a:php:php",
            #         "categories": [
            #             {
            #                 "id": 27,
            #                 "slug": "programming-languages",
            #                 "name": "Programming languages"
            #             }
            #         ]
            #     },
            #     {
            #         "slug": "tengine",
            #         "name": "Tengine",
            #         "confidence": 100,
            #         "version": null,
            #         "icon": "Tengine.png",
            #         "website": "http://tengine.taobao.org",
            #         "cpe": null,
            #         "categories": [
            #             {
            #                 "id": 22,
            #                 "slug": "web-servers",
            #                 "name": "Web servers"
            #             }
            #         ]
            #     },
            #     {
            #         "slug": "font-awesome",
            #         "name": "Font Awesome",
            #         "confidence": 100,
            #         "version": "4.7.0",
            #         "icon": "font-awesome.svg",
            #         "website": "https://fontawesome.com/",
            #         "cpe": null,
            #         "categories": [
            #             {
            #                 "id": 17,
            #                 "slug": "font-scripts",
            #                 "name": "Font scripts"
            #             }
            #         ]
            #     },
            #     {
            #         "slug": "baidu-analytics",
            #         "name": "Baidu Analytics (百度统计)",
            #         "confidence": 100,
            #         "version": null,
            #         "icon": "Baidu Tongji.png",
            #         "website": "https://tongji.baidu.com/",
            #         "cpe": null,
            #         "categories": [
            #             {
            #                 "id": 10,
            #                 "slug": "analytics",
            #                 "name": "Analytics"
            #             }
            #         ]
            #     },
            #     {
            #         "slug": "jquery",
            #         "name": "jQuery",
            #         "confidence": 100,
            #         "version": "2.0.3",
            #         "icon": "jQuery.svg",
            #         "website": "https://jquery.com",
            #         "cpe": "cpe:/a:jquery:jquery",
            #         "categories": [
            #             {
            #                 "id": 59,
            #                 "slug": "javascript-libraries",
            #                 "name": "JavaScript libraries"
            #             }
            #         ]
            #     }
            # ]
            #             '''
            app_iter = self.__parse_alyzer_res(res)
            for category, name, url, version in app_iter:
                com = Component(self.task, level, name)
                # 好奇怪，按着常理来说，这个category如果有数据那么都应该是dict, by judy 202006/24
                ctname = category.get('name')
                if ctname is None:
                    continue
                com.category = ctname
                com.url = url
                com.ver = version
                # continue
                yield com
            self.task.success_count()
        except:
            self.task.fail_count()
            self._logger.info('Warnning, currently this plug-in only runs in a docker environment')
            self._logger.error(f'Get url component error, err:{traceback.format_exc()}')
