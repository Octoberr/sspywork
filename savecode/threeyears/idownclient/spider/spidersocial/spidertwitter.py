from .spidersocialbase import SpiderSocialBase
import requests
from bs4 import BeautifulSoup
import re
import time
import random


class SpiderTwitter(SpiderSocialBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderTwitter, self).__init__(task, appcfg, clientid)
        self.islogin = re.compile(r'我们无法使用该信息搜索你的账号')
        self.maxtry = re.compile(r'你已经超过了允许尝试次数。请稍后再试')
        self.account = '+' + self.task.globaltelcode + self.task.account

    def _check_registration(self):
        """
        查询手机号是否注册了twitter
        # 中国的手机号需要加上+86
        :param account:
        :return:
        """
        post = "https://twitter.com/account/begin_password_reset"
        url = "https://twitter.com"

        data = {"account_identifier": self.account}

        with requests.Session() as s:
            r = s.get(url)
            # get auth token
            soup = BeautifulSoup(r.content, "lxml")
            AUTH_TOKEN = soup.select_one(
                "input[name=authenticity_token]")["value"]
            # update data, post and you are logged in.
            data["authenticity_token"] = AUTH_TOKEN
            s.headers.update({"accept-language": 'zh-CN,zh;q=0.9,en;q=0.8'})
            # 因为有IP限制，所以获取代理访问
            proxy = self.get_proxy()
            r = s.post(post, data=data, proxies={
                       "http": "http://{}".format(proxy)})
            # r = s.post(post, data=data, proxies=proxies)
            # r = s.post(post, data=data)
            res = r.text
            # 先判断IP是否被封了
            ipmax = self.maxtry.search(res)
            while ipmax:
                self.delete_proxy(proxy)
                # todo删除被封了的IP重新获取一个
                time.sleep(random.randint(0, 5))
                print(ipmax.group())
                proxy = self.get_proxy()
                print(proxy)
                r = s.post(post, data=data, proxies={
                           "http": "http://{}".format(proxy)})
                res = r.text
                ipmax = self.maxtry.search(res)
            else:
                notsignup = self.islogin.search(res)
                if notsignup:
                    # 如果匹配到没有注册返回false
                    resbool = False
                else:
                    # 反之返回true
                    resbool = True
        return resbool

    def get_proxy(self):
        return requests.get("http://123.207.35.36:5010/get/").text

    def delete_proxy(self, proxy):
        return requests.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy))