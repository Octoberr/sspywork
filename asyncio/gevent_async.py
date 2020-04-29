# coding:utf8
import requests
import gevent
from gevent import monkey
monkey.patch_all()      # 用于将标准库中大部分阻塞式调用修改为协作式运行


def fetch(url):
    print("get: {}".format(url))
    response = requests.get(url).content
    return url, len(response)


if __name__ == "__main__":
    g_list = list()
    for url in ["https://stackoverflow.com/", "https://www.douban.com", "https://www.github.com"]:
        g = gevent.spawn(fetch, url)
        g_list.append(g)
    gevent.joinall(g_list)
    for g in g_list:
        print(g.value)