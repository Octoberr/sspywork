"""
高匿代理测试
create by swm
2019/02/28
"""
import json
import time

import requests


class IpProxy(object):

    def __init__(self):
        pass

    def get_proxy(self):
        return requests.get(" http://127.0.0.1:5010/get/").content

    def delete_proxy(self, proxy):
        requests.get(" http://127.0.0.1:5010/delete/?proxy={}".format(proxy))

    def con_proxy(self):
        while True:
            url = 'https://httpbin.org/get?show_env=1'
            pr = self.get_proxy().decode('utf-8')
            print(pr)
            response = requests.get(url, proxies={"http": "http://{}".format(pr)})
            data = json.loads(response.text)
            print(data['origin'])
            self.delete_proxy(pr)
            time.sleep(0.5)


if __name__ == '__main__':
    ir = IpProxy()
    ir.con_proxy()
