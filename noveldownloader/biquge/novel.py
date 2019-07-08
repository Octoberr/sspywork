"""
笔趣阁的小说下载器
有不少山寨网站，认准官网
小说官网：https://www.xbiquge.cc
下载小说
输入小说首页：类似于https://www.xbiquge.cc/book/46840/
"""

import json
import requests
import re
import time
from bs4 import BeautifulSoup


class Novel(object):

    def __init__(self):
        self.ha = requests.session()
        self.cookie = '_abcde_qweasd=0; _abcde_qweasd=0; Hm_lvt_169609146ffe5972484b0957bd1b46d6=1562310935; BAIDU_SSP_lcr=https://www.baidu.com/link?url=6TtC5LGO1EKy75CrAXLzoWvDF23zq1goWuX-T3SPla7&wd=&eqid=926398c9000555aa000000025d1ef910; bdshare_firstime=1562310934656; Hm_lpvt_169609146ffe5972484b0957bd1b46d6=1562310972'
        self.links = []
        self.downloaded = self.get_downloaded()

    def save_downlaoded(self, down_links):
        """
        保存下载的连接
        :param down_links:
        :return:
        """
        with open('jianlaidownload.txt', 'w') as fp:
            fp.write(json.dumps(down_links, ensure_ascii=False))
        return

    def get_downloaded(self):
        """
        获取已经下载了的章节
        :return:
        """
        return []
        with open('jianlaidownload.txt', 'r') as fp:
            res = fp.read()
        if res == '':
            return []
        else:
            return json.loads(res)

    def get_all_downloadlinks(self, url):
        """
        获取已存在的连接
        :return:
        """
        # start_url = 'https://www.xbiquge.cc/book/13810/'
        headers = {
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            'Accept-Encoding': "gzip, deflate, br",
            'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
            'Cache-Control': "no-cache",
            'Connection': "keep-alive",
            'Cookie': self.cookie,
            'Host': "www.xbiquge.cc",
            'Pragma': "no-cache",
            'Referer': url,
            'Upgrade-Insecure-Requests': "1",
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"
        }
        res = requests.get(url, headers=headers)
        res.encoding = 'GBK'
        res_text = res.text
        re_zhangjie = re.compile('\d+\.html')
        all_zs = re_zhangjie.findall(res_text)
        self.save_downlaoded(all_zs)
        ready_downlinks = [x for x in all_zs if x not in self.downloaded]
        return ready_downlinks[2:]

    def download_link(self, lurl, downloadlinks: list):
        """
        开始按顺序下载链接
        :param downloadlinks:
        :return:
        """
        # lurl = 'https://www.xbiquge.cc/book/13810/'
        # url = 'https://www.xbiquge.cc/book/13810/26653657.html'

        headers = {
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            'Accept-Encoding': "gzip, deflate, br",
            'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
            'Cache-Control': "no-cache",
            'Connection': "keep-alive",
            'Cookie': self.cookie,
            'Host': "www.xbiquge.cc",
            'Pragma': "no-cache",
            'Referer': lurl,
            'Upgrade-Insecure-Requests': "1",
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"
        }
        self.ha.headers.update(headers)
        fp = open(f'{int(time.time())}.txt', 'a', encoding='utf-8')

        for el in downloadlinks:
            url = f'{lurl}{el}'
            print(f"开始下载:{url}")
            res = self.ha.get(url)
            res.encoding = 'gbk'
            res_text = res.text
            soup = BeautifulSoup(res_text, 'lxml')
            title: str = soup.find('div', attrs={'class': 'bookname'}).contents[1].text
            print(f'写入章节:{title}')
            fp.write(str(title.encode('utf-8').decode('utf-8')))

            content = soup.find('div', attrs={'id': 'content', 'name': 'content'}).text
            fp.write(str(content.encode('utf-8').decode('utf-8')))

        fp.close()
        return

    def start(self):
        url = input("输入小说地址：")
        alllinks = self.get_all_downloadlinks(url)
        print('开始下载')
        self.download_link(url, alllinks)


if __name__ == '__main__':
    jl = Novel()
    jl.start()
