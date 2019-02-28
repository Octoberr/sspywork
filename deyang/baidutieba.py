"""
百度贴吧爬虫
按关键字搜索贴吧，按关键字搜索帖子
"""
import base64
import csv
import datetime
import json
import queue
import re
import threading
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from commonbaby.httpaccess import HttpAccess


class BaiDuTieBa(object):

    def __init__(self):
        # self.s = requests.session()
        self.s = HttpAccess()
        self.tieba_keyword = '四川'
        self.tiezi_keyword = ['四川', '德阳']
        start_cookie = 'TIEBA_USERTYPE=8f42a94301cb125114b88e7c; wise_device=0; BAIDUID=CB7173B0D9165F60AF77E8ACE3C20897:FG=1; bdshare_firstime=1551248833930; Hm_lvt_98b9d8c2fd6608d564bf2ac2ae642948=1551248834; BDUSS=BBdHZRVnhYfnB3aGRKdUViVW9-QXFCUkVJVFUyNWdyUVRMUUpOeWxaU1oyWjFjQUFBQUFBJCQAAAAAAAAAAAEAAAA23WE5yq7UwnNlcHRlbWJlcgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJlMdlyZTHZcQV; STOKEN=621f6ba3aa1e26cbad20ecfe531ea78659a0ec1878489146ad833b226ce9e2fa; TIEBAUID=f986682cc736e76dfd7f2ee8; Hm_lpvt_98b9d8c2fd6608d564bf2ac2ae642948=1551258762'
        self.s._managedCookie.add_cookies('tieba.baidu.com', start_cookie)
        self.content_url_queue = queue.Queue()
        self.dealing_queue = []
        # 当前文件夹
        self.filepath = Path(__file__).parents[0]
        self.tiebahost = 'https://tieba.baidu.com'

    def out_formate(self, s: str) -> str:
        try:
            return base64.b64encode(s.encode()).decode('utf-8')
        except Exception as ex:
            s = repr(s)
            return base64.b64encode(s.encode()).decode('utf-8')

    # def update_cookie(self, res: requests.Response, headers):
    #     """
    #     更新cookie,和refer_url
    #     也就相当于更新了cookie
    #     :return:
    #     """
    #     if res is not None:
    #         cookiedict = res.cookies.get_dict()
    #         cookie_string = ';'.join([str(x) + '=' + str(y) for x, y in cookiedict.items()])
    #         self.start_cookie += cookie_string
    #         headers['Cookie'] += self.start_cookie
    #     return headers

    def get_start_url(self):
        return f'http://tieba.baidu.com/f?kw={self.tieba_keyword}&ie=utf-8&pn=0'

    def judge_key_world_in_title(self, title):
        res = False
        try:
            for el in self.tiezi_keyword:
                if el in title:
                    res = True
        except:
            res = False
        return res

    def get_download_links(self):
        """
        获取需要下载的链接
        :return:
        """
        # http://tieba.baidu.com/f?kw=%E5%9B%9B%E5%B7%9D&ie=utf-8&pn=0
        # 每次url的增长是50
        # 从启始页开始拿
        next_page = True
        nextpagenum = 0
        # 最后一页
        last_page = None
        next_url = self.get_start_url()
        re_title = re.compile(
            '<a rel="noreferrer" href="(.+?)" title="(.+?)" target="_blank" class="j_th_tit ">.+?</a>')
        re_next_page = re.compile('pn=(\d+)')
        while next_page:
            try:
                response = self.s.getstring(next_url, headers='''
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
Cache-Control: no-cache
Host: tieba.baidu.com
Pragma: no-cache
Proxy-Connection: keep-alive
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36''')
                # 更新cookie
                # headers = self.update_cookie(response, headers)
                all_find = re_title.findall(response)
                if len(all_find) > 0:
                    for el_title in all_find:
                        is_key_in = self.judge_key_world_in_title(el_title[1])
                        if is_key_in:
                            if not el_title[0].startswith('http://'):
                                content_url = el_title[0]
                                self.content_url_queue.put((content_url, el_title[1]))
                else:
                    print(f"没有获取到此页面,{next_url}")
                    nextpagenum += 50
                    next_url = f'http://tieba.baidu.com/f?kw={self.tieba_keyword}&ie=utf-8&pn={nextpagenum}'
                    print(f'now page num:{nextpagenum-50}, next_url:{next_url}')
                    continue
                next_page_all = re_next_page.findall(response)
                # 只用一次
                if last_page is None:
                    last_page = next_page_all[-1]
                # if int(next_page_all[-2]) < int(last_page):
                if nextpagenum < int(last_page):
                    # nextpagenum = next_page_all[-2]
                    nextpagenum +=50
                    next_url = f'http://tieba.baidu.com/f?kw={self.tieba_keyword}&ie=utf-8&pn={nextpagenum}'
                    print(f'next url:{next_url}')
                else:
                    next_page = False
                    break
            except Exception as err:
                nextpagenum += 50
                next_url = f'http://tieba.baidu.com/f?kw={self.tieba_keyword}&ie=utf-8&pn={nextpagenum}'
                print(f'error page:{nextpagenum - 50}, now go next_url:{next_url},error:{err}')
                continue

    def get_reply(self, tid, pn, refer, title) -> iter:
        url = "https://tieba.baidu.com/p/totalComment"

        querystring = {"tid": tid, "fid": "1", "pn": pn}

        response = self.s.getstring(url, headers='''
Accept: application/json, text/javascript, */*; q=0.01
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
Cache-Control: no-cache
Connection: keep-alive
Host: tieba.baidu.com
Pragma: no-cache
Referer: {}
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
X-Requested-With: XMLHttpRequest'''.format(refer), params=querystring)
        # 更新下cookie,虽然没有用
        # headers = self.update_cookie(response, headers)

        data = json.loads(response)
        if data.get('errno') != 0 or data.get('errmsg') != 'success':
            return []
        c_list = data.get('data').get('comment_list')
        if c_list is None:
            return []
        if len(c_list) == 0:
            return []
        for key, value in c_list.items():
            for el in value.get('comment_info'):
                try:
                    write_line = {}
                    s_id = el.get('comment_id')
                    post_id = el.get('post_id')
                    author = el.get('username')
                    content = el.get('content')
                    if content is None or content == '':
                        continue
                    g_time = el.get('now_time')  # unixtime
                    g_d_time = str(datetime.datetime.fromtimestamp(g_time))
                    write_line['id'] = s_id
                    write_line['replyid'] = post_id
                    write_line['author'] = self.out_formate(author)
                    write_line['title'] = self.out_formate(title)
                    write_line['stars'] = None
                    write_line['content'] = self.out_formate(content)
                    write_line['resources'] = None
                    write_line['createtime'] = g_d_time
                    write_line['updatetime'] = None
                    write_line['likes'] = None
                    yield write_line
                except Exception as err:
                    print(f"获取当前页的评论出错，err:{err}")
                    continue

    def get_content_info(self):
        re_next_page = re.compile('<a href="(.+?)">下一页</a>')
        no_data_times = 0
        with threading.Lock():
            csvfile = open(self.tieba_keyword + '.csv', 'a', newline='')
            fieldnames = ['id', 'replyid', 'author', 'title', 'stars', 'content', 'resources', 'createtime', 'updatetime',
                          'likes']

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            # writer.writeheader()

        while True:
            if no_data_times > 50:
                print("no data to crawel")
                break

            if self.content_url_queue.empty():
                time.sleep(3)
                no_data_times += 1
                continue

            url_info = self.content_url_queue.get()

            url = url_info[0]
            title = url_info[1]
            has_next = True
            next_url = None
            # 拿评论需要的信息
            pn = 1
            tid = re.search('\d+', url).group()

            while has_next:
                # 第一次访问url
                try:
                    if next_url is None:
                        next_url = self.tiebahost + url
                    response = self.s.getstring(next_url, headers='''
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
Cache-Control: no-cache
Host: tieba.baidu.com
Pragma: no-cache
Proxy-Connection: keep-alive
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36''')
                    # 更新cookie
                    # headers = self.update_cookie(response, headers)

                    soup = BeautifulSoup(response, 'lxml')
                    get_div_info = soup.find('div', attrs={'class': 'p_postlist'})
                    all_content_divs = get_div_info.contents
                    for content_div in all_content_divs:
                        try:
                            write_line = {}
                            data_info = content_div.get('data-field')
                            if data_info is None:
                                continue
                            data = json.loads(data_info)
                            floorid = data.get('content').get('post_id')
                            author = data.get('author').get('user_name')

                            re_get_time = re.search('\d{4}-\d{2}-\d{2} \d{2}:\d{2}', str(content_div))
                            if re_get_time:
                                get_time = re_get_time.group() + ':00'
                                write_line['createtime'] = get_time

                            # 文本内容和图片
                            content_info = content_div.find('div', attrs={'class': re.compile('.+?j_d_post_content.+?')})
                            content = content_info.text.strip()
                            imgs_info = content_info.find_all('img', attrs={'class': 'BDE_Image'})
                            if content is None and len(imgs_info)==0:
                                continue
                            if len(imgs_info) ==0:
                                resources = []
                                for img_info in imgs_info:
                                    img = img_info.get('src')
                                    resources.append(img)
                                write_line['resources'] = self.out_formate(json.dumps(resources))
                            # 数据写入
                            write_line['id'] = floorid
                            write_line['replyid'] = None
                            write_line['author'] = self.out_formate(author)
                            write_line['title'] = self.out_formate(title)
                            write_line['stars'] = None
                            write_line['content'] = self.out_formate(content)
                            write_line['updatetime'] = None
                            write_line['likes'] = None
                            with threading.Lock():
                                writer.writerow(write_line)
                            print(f'Write a line:{write_line}')
                        except Exception as err:
                            print(f"获取某个楼层出错，err:{err}")
                            continue

                    # 获取评论
                    for comm in self.get_reply(tid, pn, url, title):
                        with threading.Lock():
                            writer.writerow(comm)
                        print(f'Write a commit:{comm}')
                    # 获取下一页
                    nextpage = re_next_page.search(response)
                    if nextpage:
                        next_url = self.tiebahost + nextpage.group(1)
                        pn += 1
                    else:
                        has_next = False
                except Exception as err:
                    print(f"获取这页的url出错:{url}, err:{err}")
                    has_next = False

            self.content_url_queue.task_done()
        print("complex")
        csvfile.close()

    def start(self):
        csvfile = open(self.tieba_keyword + '.csv', 'a', newline='')
        fieldnames = ['id', 'replyid', 'author', 'title', 'stars', 'content', 'resources', 'createtime', 'updatetime',
                      'likes']

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        csvfile.close()

        thread1 = threading.Thread(target=self.get_download_links, name="get_download_link")
        thread1.start()
        for i in range(3):
            threads = threading.Thread(target=self.get_content_info, name="get_comments")
            threads.start()


if __name__ == '__main__':
    bdt = BaiDuTieBa()
    # bdt.get_download_links()
    bdt.start()
    # bdt.get_content_info()
