import random
import re
import csv
import time

import requests
from bs4 import BeautifulSoup


class DeYang(object):

    def __init__(self):
        pass

    def get_proxy(self):
        return requests.get(" http://123.207.35.36:5010/get/").content

    def delete_proxy(self, proxy):
        requests.get(" http://123.207.35.36:5010/delete/?proxy={}".format(proxy))

    def _get_headers(self):
        usr = [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
            'Mozilla/5.0 (Linux; U; Android 4.0; en-us; GT-I9300 Build/IMM76D) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Mobile Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:62.0) Gecko/20100101 Firefox/62.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134'
        ]
        headers = {
            # 'Cookie': self.cookie,
            'User-Agent': random.choice(usr)
        }
        return headers

    def get_new_house_price(self):
        url = "https://de.fang.anjuke.com/loupan/all/"
        response = requests.request("GET", url, headers=self._get_headers())
        res_text = response.text
        soup = BeautifulSoup(res_text, 'lxml')
        idives = soup.find_all('dl')
        # print(idives)
        for one_dl in idives:
            one_dl = str(one_dl)
            re_name = re.compile('<span class="g-overflow">(.+?)</span>')
            name = re_name.search(one_dl)
            if name:
                print(name.group(1))
            else:
                continue
            re_area = re.compile('<div class="jianmian g-overflow">(.+?)</div>')
            area = re_area.search(one_dl)
            if area:
                print(area.group(1))
            re_price = re.compile('\d{4,8}')
            price = re_price.search(one_dl)
            print(price.group())
            # name = one_dl.span.string
            # print(name)
            # size = one_dl.div.string
            # print(size)
            # area = one_dl.dd.get_text()
            # print(area)
            # price = one_dl.select('dd[class="flexbox average-price"]')[0].get_text()
            # print(price)
        all_page_link = soup.select('dd[class="go-page clearfix"]')[0]
        link = all_page_link.find_all('a')
        for o_l in link:
            print(o_l.get('href'))

    def get_all_hosue_info(self):
        errorcount = 0
        csvfile = open('deyang.csv', 'w', newline='', encoding='GBK')
        fieldnames = ['areaname', 'price']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        proxy = self.get_proxy()
        starturl = 'https://www.anjuke.com/deyang/cm/'
        response = requests.get(starturl, headers=self._get_headers(), proxies={"http": "http://{}".format(proxy)})
        res_text = response.text
        re_nextpage = re.compile('<a href="(.+?)"><span class="nextpage"><ins>下一页</ins>')
        soup = BeautifulSoup(response.text, 'lxml')
        housinfo_div = soup.select('ul[class=P3]')[0]
        all_li = housinfo_div.find_all('li')
        for li in all_li:
            all_a = li.find_all('a')
            for one_a in all_a:
                name = one_a.string
                href = one_a.get('href')
                price = self.get_house_info(href, proxy)
                if price == '暂无价格数据':
                    errorcount += 1
                if errorcount > 1:
                    self.delete_proxy(proxy)
                    proxy = self.get_proxy()
                    errorcount = 0
                    continue
                writer.writerow({'areaname': name, 'price': price})
                # self.write_file(name, price)
                print(f'get:{name}, price:{price}')
                time.sleep(random.randint(3, 9))
        while True:
            next_page = re_nextpage.search(res_text)
            self.delete_proxy(proxy)
            proxy = self.get_proxy()
            if next_page:
                try:
                    url = next_page.group(1)
                    print(f'Get a url:\n{url}')
                    response = requests.get(url, headers=self._get_headers())
                    res_text = response.text
                    soup = BeautifulSoup(response.text, 'lxml')
                    housinfo_div = soup.select('ul[class=P3]')[0]
                    all_li = housinfo_div.find_all('li')
                    for li in all_li:
                        all_a = li.find_all('a')
                        for one_a in all_a:
                            name = one_a.string
                            href = one_a.get('href')
                            price = self.get_house_info(href, proxy)
                            if price == '暂无价格数据':
                                errorcount += 1
                            if errorcount > 1:
                                self.delete_proxy(proxy)
                                proxy = self.get_proxy()
                                errorcount = 0
                                continue
                            writer.writerow({'areaname': name, 'price': price})
                            # self.write_file(name, price)
                            print(f'get:{name}, price:{price}')
                            time.sleep(random.randint(3, 9))
                except:
                    continue
            else:
                break
        csvfile.close()

    def get_house_info(self, href, prx):
        # url = 'https://www.anjuke.com/deyang/cm707309/'
        response = requests.get(href, headers=self._get_headers(), proxies={"http": "http://{}".format(prx)})
        res_text = response.text
        re_price = re.compile('<span class="price">(.+?)</span>')
        price = re_price.search(res_text)
        if price:
            re_num = re.compile('\d+')
            num = re_num.search(price.group(1))
            if num:
                return num.group()
            else:
                return '没有收录该小区价格'
        else:
            return '暂无价格数据'


if __name__ == '__main__':
    dy = DeYang()
    # dy.get_new_house_price()
    # dy.get_all_hosue()
    # dy.get_house_info()
    dy.get_all_hosue_info()
    # dy.write_file()
