"""
scout的一个插件
"""
import re
import threading
import traceback

from commonbaby.httpaccess import HttpAccess

from .scoutplugbase import ScoutPlugBase


class SecurityTrails(ScoutPlugBase):
    '''securitytrails'''

    _re_domain_validation = re.compile(r'^[a-zA-Z-\.]+$', re.S)

    def __init__(self):
        ScoutPlugBase.__init__(self)

        self._ha: HttpAccess = HttpAccess()
        self._host: str = 'securitytrails.com'

    def _access_search_page(self) -> bool:
        """初始化搜索页面"""
        try:
            return False
            url = 'https://securitytrails.com'
            html = self._ha.getstring(url, headers='''
            ''')

        except Exception:
            self._logger.error("Access search page error: {}".format(
                traceback.format_exc()))

    def get_subdomain(self, domain: str) -> iter:
        """获取指定域名的子域名，迭代返回 每个子域名（str）"""
        try:
            # 太复杂了，耗时太久，先放弃了
            return []
            if not isinstance(
                    domain, str
            ) or not SecurityTrails._re_domain_validation.match(domain):
                return

            if not self._access_search_page():
                return

        except Exception:
            self._logger.error("Get subdomain of {} error: {}".format(
                domain, traceback.format_exc()))

    def get_ip_history(self) -> iter:
        pass
