"""
https://www.xbiquge.cc/book/6811/
"""
import json
import requests
import re
from bs4 import BeautifulSoup


class JianLai(object):

    def __init__(self):
        self.ha = requests.session()
        self.cookie = 'Hm_lvt_d3e5f4edf98e3ec0ced6fc2c39b60bae=1562211636,1562212519,1562220269,1562221139; jieqiVisitTime=jieqiArticlesearchTime%3D1562221294; Hm_lpvt_d3e5f4edf98e3ec0ced6fc2c39b60bae=1562221294; jieqiVisitId=article_articleviews%3D13810%7C6811'
        self.links = []
        self.downloaded = self.get_downloaded()

    def save_downlaoded(self, down_links):
        """
        保存下载的连接
        :param down_links:
        :return:
        """
        with open('qinyuniandownload.txt', 'w') as fp:
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

    def get_all_downloadlinks(self):
        """
        获取已存在的连接
        :return:
        """
        start_url = 'https://www.xbiquge.cc/book/6811/'
        headers = {
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            'Accept-Encoding': "gzip, deflate, br",
            'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
            'Cache-Control': "no-cache",
            'Connection': "keep-alive",
            'Cookie': self.cookie,
            'Host': "www.xbiquge.cc",
            'Pragma': "no-cache",
            'Referer': "https://www.xbiquge.cc/book/6811/",
            'Upgrade-Insecure-Requests': "1",
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"
        }
        res = requests.get(start_url, headers=headers)
        res.encoding = 'GBK'
        res_text = res.text
        re_zhangjie = re.compile('\d+\.html')
        all_zs = re_zhangjie.findall(res_text)
        self.save_downlaoded(all_zs)
        ready_downlinks = [x for x in all_zs if x not in self.downloaded]
        return ready_downlinks[2:]

    def download_link(self, downloadlinks: list):
        """
        开始按顺序下载链接
        :param downloadlinks:
        :return:
        """
        lurl = 'https://www.xbiquge.cc/book/6811/'
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
            'Referer': "https://www.xbiquge.cc/book/6811/",
            'Upgrade-Insecure-Requests': "1",
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"
        }
        self.ha.headers.update(headers)
        fp = open('庆余年.txt', 'a', encoding='utf-8')

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
        alllinks = self.get_all_downloadlinks()
        print('开始下载')
        self.download_link(alllinks)


if __name__ == '__main__':
    jl = JianLai()
    jl.start()

