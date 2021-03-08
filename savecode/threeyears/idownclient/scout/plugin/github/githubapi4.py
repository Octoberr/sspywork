"""github"""

# -*- coding:utf-8 -*-

import json
import threading
import traceback

from commonbaby.httpaccess import HttpAccess
from commonbaby.mslog import MsLogger, MsLogManager


class GitHubApi4:
    """The github api v4\n
    token: you need a token to get access, like a personal token."""

    HOST = "https://api.github.com/graphql"

    _header = """
    Accept: */*
    Accept-Encoding: gzip, deflate
    Accept-Language: en-US,en;q=0.9,zh;q=0.8
    Cache-Control: no-cache
    Connection: keep-alive
    Pragma: no-cache
    User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36
    Authorization: Bearer %s"""

    # Content-Type: application/json

    # fb0cd5239c2afcc96b438b6b673bf96f715d4386

    def __init__(self, token: str):
        assert isinstance(token, str)
        self._token: str = token
        self._header = self._header % self._token

        self._is_logined: bool = False
        self._login_locker = threading.RLock()

        self._logger: MsLogger = MsLogManager.get_logger("GitAPIv4")
        self._ha: HttpAccess = HttpAccess()

        self._user_name: str = None
        self._user_login: str = None
        self._user_id: str = None

    def login(self) -> bool:
        """try login, return whether succeed"""
        if self._is_logined:
            return True
        with self._login_locker:
            if self._is_logined:
                return True

            if self._login():
                self._is_logined = True
                self._logger.info("Github api login succeed: id:{}".format(
                    self._user_id))
            else:
                self._logger.info("Github api login failed")

        return self._is_logined

    def _login(self) -> bool:
        """login"""
        res: bool = False
        try:
            ql = """
query {
  viewer {
    id
    login
    name
  }
}
"""

            html = self._query(ql)
            if html is None:
                return res

            sj = json.loads(html)
            if sj is None:
                return res

            if not sj.__contains__("data") or \
               not sj["data"].__contains__("viewer"):
                return res

            sjviwer = sj["data"]["viewer"]
            if not sjviwer.__contains__("login") or \
               not sjviwer.__contains__("name") or \
               not sjviwer.__contains__("id"):
                return res

            self._user_id = sjviwer["id"]
            self._user_name = sjviwer["name"]
            self._user_login = sjviwer["login"]

            res = True

        except Exception:
            self._logger.error("Login error: {}".format(
                traceback.format_exc()))
        return res

    def _query(self, graphql: str) -> str:
        """query github, return response json data.\n
        return None if failed."""

        dql = {"query": "{}".format(graphql.strip())}
        strdql = json.dumps(dql)
        html = self._ha.getstring(self.HOST, strdql, headers=self._header)
        return html
