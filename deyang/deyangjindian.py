import base64
import csv
import json
import re
import threading

import requests
import queue
from bs4 import BeautifulSoup
from pathlib import Path
from commonbaby.httpaccess import HttpAccess


class DeYang(object):
    imagesnumbel = 0

    def __init__(self):
        self._ha = HttpAccess()
        cookies = '_RF1=101.204.79.78; _RSG=7t4K9DysapAAy3T6IzZvP9; _RDG=28c3a46e16bd9527e206056f639f93f12d; _RGUID=ace4dbc3-4950-4dc7-9679-8fd486743f0a; ASP.NET_SessionSvc=MTAuOC4xODkuNTV8OTA5MHxqaW5xaWFvfGRlZmF1bHR8MTU0NzYzNTY5NDYxNA; bdshare_firstime=1550397871920; MKT_Pagesource=PC; _ga=GA1.2.1090470229.1550397875; _gid=GA1.2.111071048.1550397875; _bfa=1.1550397832747.3uetxn.1.1550397832747.1550397832747.1.4; _bfs=1.4; gad_city=be2e953e1ae09d16d9cc90a550611388; __zpspc=9.1.1550397884.1550397884.1%234%7C%7C%7C%7C%7C%23; _jzqco=%7C%7C%7C%7C1550397884384%7C1.1018365145.1550397884256.1550397884256.1550397884256.1550397884256.1550397884256.0.0.0.1.1; _bfi=p1%3D290510%26p2%3D290546%26v1%3D4%26v2%3D3; appFloatCnt=3'
        self._ha._managedCookie.add_cookies('ctrip.com', cookies)
        self.page_url = queue.Queue()
        self.que_dealing = []
        # 当前文件夹
        self.filepath = Path(__file__).parents[0]

    def out_formate(self, s: str) -> str:
        try:
            return base64.b64encode(s.encode()).decode('utf-8')
        except Exception as ex:
            s = repr(s)
            return base64.b64encode(s.encode()).decode('utf-8')

    def get_ctrip_link(self):
        re_name = re.compile('<a target="_blank" href="(/.+?)" title="(.+?)">.+?</a>')
        for n in range(5):
            url = f"http://you.ctrip.com/sight/deyang462/s0-p{n + 1}.html"
            html_2 = self._ha.getstring(url, headers='''
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
Cache-Control: no-cache
Host: you.ctrip.com
Pragma: no-cache
Proxy-Connection: keep-alive
Referer: http://you.ctrip.com/
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36''')

            name_info = re_name.findall(html_2)

            for name_one in name_info:
                self.page_url.put(name_one)
            print("所有要下载的链接均已获得")
        return

    def get_content_info(self, poid, did, dname, pageall, rid, dirloc: Path):
        url = "http://you.ctrip.com/destinationsite/TTDSecond/SharedView/AsynCommentView"
        for page in range(int(pageall)):
            payload = "poiID={}&districtId={}&districtEName={}&" \
                      "pagenow={}&order=3.0&star=0.0&tourist=0.0" \
                      "&resourceId={}&resourcetype=2".format(poid, did, dname, page+1, rid)
            page_html = self._ha.getstring(url, payload, headers='''
Accept: */*
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
Cache-Control: no-cache
Content-Length: 125
Content-Type: application/x-www-form-urlencoded
Host: you.ctrip.com
Origin: http://you.ctrip.com
Pragma: no-cache
Proxy-Connection: keep-alive
Referer: http://you.ctrip.com/
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36
X-Requested-With: XMLHttpRequest
            ''')

            soup = BeautifulSoup(page_html, 'lxml')
            all_username = soup.find_all('div', attrs={"class": "userimg"})
            comments_divs = soup.find_all('div', attrs={"class": "comment_ctrip"})
            all_ul = comments_divs[0].find_all('ul')
            for i in range(len(all_ul)):
                try:
                    line = {}
                    name = all_username[i].get_text(strip=True)
                    line['author'] = self.out_formate(name)
                    all_lis = all_ul[i].find_all('li')
                    stars_info = all_lis[0].get_text()
                    stars = re.findall('\d', stars_info)
                    line['title'] = None
                    if len(stars) > 0:
                        get_starts = stars[-1]
                        line['stars'] = get_starts + '/5'
                    else:
                        line['stars'] = None
                    des = all_lis[1].get_text(strip=True)
                    line['content'] = self.out_formate(des)
                    if len(all_lis) == 4:
                        all_pics = []
                        # 有图片
                        all_a = all_lis[2].find_all('a')
                        for a_one in all_a:
                            with threading.Lock():
                                jpg_url = a_one.get('href')
                                # 下载图片
                                jpg_locname = str(DeYang.imagesnumbel) + '.jpg'
                                img = requests.get(jpg_url)
                                jpg_loc: Path = dirloc / jpg_locname
                                with jpg_loc.open('ab') as f:
                                    f.write(img.content)
                                    f.close()
                                print(f"download complete:{jpg_locname}")
                                all_pics.append(jpg_locname)
                                DeYang.imagesnumbel += 1
                        line['pictures'] = json.dumps(all_pics)
                    else:
                        line['pictures'] = None
                    others_info = all_lis[-1]
                    useful_info = others_info.get_text(strip=True)
                    useful = re.findall('\（(\d+)\）', useful_info)
                    if len(useful) > 0:
                        useful_res = useful[-1]
                    else:
                        useful_res = None
                    time = others_info.find('span', attrs={"class": "time_line"}).get_text(strip=True) + ' 00:00:00'
                    line['createtime'] = None
                    line['updatetime'] = None
                    line['time'] = time
                    line['replyto'] = None
                    line['likes'] = useful_res
                    yield line
                except Exception as ex:
                    print(f'解析一行出错:{ex}')
                    continue

    def get_content(self):
        re_content_pages = re.compile('<b class="numpage">(\d+)</b>')
        re_poid = re.compile('<a href="/dianping/edit/(\d+).html" class="b_orange_m">')
        while True:
            # 去队列里取一个url('url', 'name')
            try:
                url_info = self.page_url.get()
                if url_info in self.que_dealing:
                    print("这个url正在下载或者已经下载完成，跳过")
                    continue
                # 放进正在处理的列表里
                self.que_dealing.append(url_info)
                url = url_info[0]
                dirname = url_info[1]
                dir_loc = self.filepath / dirname
                dir_loc.mkdir(exist_ok=True)
                csvfilename = dir_loc / (dirname + '.csv')
                csvfile = open(str(csvfilename), 'w', newline='')
                fieldnames = ['author', 'title', 'stars', 'content', 'pictures', 'createtime', 'updatetime', 'time',
                              'replyto', 'likes']

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                infos = url.split('/')
                dname = re.findall('[a-zA-Z]+', infos[2])[0]
                did = re.findall('\d+', infos[2])[0]
                rid = re.findall('\d+', infos[-1])[0]
                url = "http://you.ctrip.com" + url
                # proxy = self.get_proxy()
                # response = requests.get(url, headers=self.get_headers(url))
                response = self._ha.getstring(url, headers='''
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
Cache-Control: no-cache
Host: you.ctrip.com
Pragma: no-cache
Proxy-Connection: keep-alive
Referer: http://you.ctrip.com/
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36''')
                pages = re_content_pages.findall(response)
                if len(pages) == 0:
                    pages = 1
                else:
                    pages = pages[0]
                poid = re_poid.findall(response)[0]
                getline = self.get_content_info(poid, did, dname, pages, rid, dir_loc)
                for a_line in getline:
                    print(f"获取到一行数据:{a_line}")
                    try:
                        writer.writerow(a_line)
                    except Exception as err:
                        print(f"Write line error:{err}\nline:{a_line}")
                        continue
                self.page_url.task_done()
                # 最后所有任务执行完成后break
                if self.page_url.empty():
                    break
            except Exception as err:
                print(f"获取一个url出错,url:{url}, name:{dirname}, error:{err}")
                continue
                # self.delete_proxy(proxy)
        print("complte")
        return

    def start(self):
        thread1 = threading.Thread(target=self.get_ctrip_link, name="get_start_links")
        thread1.start()
        for i in range(10):
            threads = threading.Thread(target=self.get_content, name="writeinfo")
            threads.start()


if __name__ == '__main__':
    de = DeYang()
    de.start()
    # de.get_content()
