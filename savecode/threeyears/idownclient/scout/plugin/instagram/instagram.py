"""
Instagram插件: 有搜索接口可用
"""
import json
import traceback

import requests
from commonbaby.httpaccess.httpaccess import HttpAccess

from datacontract import IscoutTask
from idownclient.clientdatafeedback.scoutdatafeedback import NetworkProfile
from idownclient.scout.plugin.scoutplugbase import ScoutPlugBase


class Instagram(ScoutPlugBase):
    """Instagram info search"""

    def __init__(self, task: IscoutTask):
        ScoutPlugBase.__init__(self)
        self.task = task
        self._ha: HttpAccess = HttpAccess()

        self.basic_url = "https://www.instagram.com/"
        self.headers = """
                    accept: */*,
                    accept-encoding: gzip, deflate, br,
                    accept-language: zh-CN,zh;q=0.9,
                    user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36,
                    """
        # 搜索栏api
        self.searchBox_api = 'https://www.instagram.com/web/search/topsearch/?context=blended&query={}&include_reel=true'
        # 用户数据api
        self.userData_api = 'https://www.instagram.com/{}/?__a=1'

        self.source = "instagram"
        self.reason = "instagram身份落地"

    # #######################################
    # 设置一个判断
    def judgment_url(self, query: str, level: int, reason: str):
        if query is None or query == "":
            self._logger.error(f'Invalid query for search_by_url, error: {query}')
            return
        if 27 <= len(query) <= 52:
            return self.search_by_url(query, level, reason)
        else:
            return self.judgment_userid(query, level, reason)

    def judgment_userid(self, query: str, level: int, reason: str):
        if query is None or query == "":
            self._logger.error(f'Invalid query for search_by_userid, error: {query}')
            return
        if 5 <= len(query) <= 26:
            return self.search_by_userid(query, level, reason)
        else:
            return

    def judgment_keyword(self, query: str, level: int, reason: str):
        if query is None or query == "":
            self._logger.error(f'Invalid query for search_keyword, error: {query}')
            return
        if 1 <= len(query) < 5:
            return self.search_keyword(query, level, reason)

    # #######################################
    # 明确知道_用户名
    def search_by_userid(self, userid: str, level: int, reason: str):
        """"根据 用户名(userid) 搜索用户
        如: jaychou ; jjlin 之类的
        """
        # 暂且判定为 正常用户名 的长度条件
        if userid is None or userid == "" or not 5 <= len(userid) <= 26:
            self._logger.error(f'Invalid userid for instagram search, error: {userid}')
            return
        if not userid.startswith('https://'):
            self._logger.info("userid matches search rules√")
            self._logger.info(f"Get a userid to start search...: {userid}")

        return self._search_userid(userid, level, reason)

    # 明确知道_用户主页url
    def search_by_url(self, url: str, level: int, reason: str):
        """"根据 用户主页URL搜索用户
        如: https://www.instagram.com/jaychou/
        """
        # 暂且判定为 url 的长度条件
        if url is None or url == "" or not 27 <= len(url) <= 52:  # len(self.basic_url)为26
            self._logger.error(f'Invalid url for instagram search: {url}')
            return
        if url.startswith("https://www."):
            self._logger.info("url matches search rules√")
            self._logger.info(f"Get a userUrl and start search...: {url}")
            if url.endswith('/'):
                keyword = url.split('/')[-2]
            else:
                keyword = url.split('/')[-1]

            # 提取url结尾的userid, 拼接成对应数据url
            data_url = self.basic_url + f"{keyword}" + "/?__a=1"
            return self._search_url(data_url, level, reason)

    # 模糊搜索
    def search_keyword(self, keyword: str, level: int, reason: str):
        """(模糊)搜索,搜索userid相关的用户,默认取前10个"""
        # 暂且判定为 模糊搜索 的长度条件
        if keyword is None or keyword == "" or not 1 <= len(keyword) < 5:
            self._logger.error(f'Invalid keyword for instagram search, error: {keyword}')
            return
        if not keyword.startswith('https://') or keyword.startswith('http://'):
            self._logger.info("keyword matches search rules√")
            self._logger.info("Get a keyword, Start searching for related users")

            return self._search_keyword(keyword, level, reason)

    # #######################################
    # to get user(去拿用户)
    def _search_userid(self, userid: str, level: int, reason) -> iter:
        """通过 userid 搜索用户;  ->返回NetorkProfile"""
        if not isinstance(userid, str):
            self._logger.error("Invalid userid")
            return
        res: NetworkProfile = self.__get_user_by_userid(userid, reason)
        return res

    def _search_url(self, userurl: str, level: int, reason) -> iter:
        """通过 url 搜索用户;  ->返回NetorkProfile"""
        if not isinstance(userurl, str):
            self._logger.error("Invalid userurl")
            return
        res: NetworkProfile = self.__get_user_by_url(userurl, reason)
        return res

    def _search_keyword(self, keyword: str, level: int, reason) -> iter:
        """通过 userid 搜索用户;  ->返回NetorkProfile; userid"""
        if not isinstance(keyword, str):
            self._logger.error("Invalid keyword")
            return
        return self.__get_user_by_keyword(keyword, reason)

    # #######################################
    # ensure user(确定拿到用户名)
    def __get_user_by_userid(self, userid: str, reason: str) -> NetworkProfile:
        """请求api接口,提取用户数据"""
        try:
            # 用户数据api接口
            user_home_url = self.userData_api.format(userid)  # 拿用户名,拼接成用户主页url
            return self.__get_user_by_url(user_home_url, reason)

        except Exception:
            self._logger.error(f"Get user by userid error: {traceback.format_exc()}")

    def __get_user_by_url(self, userurl: str, reason: str) -> NetworkProfile:
        """通过url 确定用户"""
        try:
            # 请求用户数据api,获取用户数据
            self._logger.info(f"Start requesting user data: {userurl}")
            html = requests.get(userurl, self.headers)
            if html is None or html == "":
                return
            for p_info in self.__parse_user_profile(html.text):
                return p_info

        except Exception:
            self._logger.error(f"Get user by url error: {traceback.format_exc()}")

    def __get_user_by_keyword(self, keyword: str, reason: str) -> NetworkProfile:
        """请求 搜索栏api接口,获取关键字 相关的用户 (列表)"""
        try:
            # 搜索栏api接口,获取到一堆{关键字}相关的用户
            url = self.searchBox_api.format(keyword)
            users_li_info = requests.get(url, self.headers)
            if users_li_info is None or users_li_info == "":
                return

            start = 0
            stop = 10
            js_user_li_data = json.loads(users_li_info.text)
            if js_user_li_data:
                # 默认取前10个用户(列表)
                users = js_user_li_data["users"][start:stop]
                for user in users:
                    username = user['user']['username']  # 取到用户名(唯一的)
                    user_home_url = self.userData_api.format(username)  # 拼接成用户主页url

                    yield self.__get_user_by_url(user_home_url, reason)

        except Exception:
            self._logger.error(f"Get user by keyword error: {traceback.format_exc()}")

    # #######################################
    # parse user(解析用户资料)
    def __parse_user_profile(self, html: str):
        """
        解析用户个人资料
        :param html:
        :return:
        """
        js_html = json.loads(html)
        if js_html['graphql']:
            user = js_html['graphql']['user']
            username = user['username']
            profile = NetworkProfile(username, username, 'instagram')
            profile.networkid = None  # 从当前接口中,是没有其他关联的账号的
            profile.userid = username  # 是唯一的
            # profile.user_id = user['id']  # id值(数字)
            profile.url = self.basic_url + f'{username}'  # 用户主页链接
            profile.source = self.source
            profile.reason = self.reason
            profile.emails = None
            profile.phones = None
            profile.nickname = username
            profile.gender = None
            profile.birthday = None
            profile.address = None
            profile.profile_pic = self.__handling_user_avatar(user['profile_pic_url_hd'])
            # 以下是其他详情details
            detail = dict()
            detail['biography'] = user['biography']  # 自我介绍
            detail['posts'] = user['edge_owner_to_timeline_media']['count']  # 发帖数
            detail['fans'] = user['edge_followed_by']['count']  # 粉丝数
            detail['follow'] = user['edge_follow']['count']  # 正在关注
            detail['full_name'] = user['full_name']  # 全名
            detail['is_verified'] = user['is_verified']  # 是否验证
            detail['external_url'] = user['external_url']  # 外部链接(如: youtube),也可能没有
            detail['profile_pic_url'] = user['profile_pic_url_hd']  # 高清头像url

            profile._details = f'{detail}'.strip()
            yield profile

    # base64处理下用户头像
    def __handling_user_avatar(self, profile_pic_url_hd):
        """base64处理用户头像"""
        self._logger.info("Get a user avatar and start processing")
        try:
            res = requests.get(profile_pic_url_hd)
            res_data = res.content
            return res_data
            # str_data = helper_str.base64bytes(res_data)
            # return '?utf-8?b?' + str_data

        except Exception:
            self._logger.error("Download avatar error: {}".format(traceback.format_exc()))
            # return pic_url
