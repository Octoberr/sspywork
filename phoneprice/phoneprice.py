import csv
import random
import re
import time

from bs4 import BeautifulSoup

import requests


class PhonePrice(object):

    def __init__(self):
        pass

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

    def get_proxy(self):
        return requests.get(" http://123.207.35.36:5010/get/").content

    def delete_proxy(self, proxy):
        requests.get(" http://123.207.35.36:5010/delete/?proxy={}".format(proxy))

    def get_phone_dic(self, url):
        # url = 'https://product.pconline.com.cn/mobile/apple/1116047.html'
        response = requests.get(url, headers=self._get_headers())
        res_text = response.text
        phone_dic_res = {}
        soup = BeautifulSoup(res_text, 'lxml')
        infodiv = soup.select('div[class=crumb]')[0]
        factory_info = infodiv.find_all('a')[-1]
        factory = factory_info['title'].replace('手机大全', '')
        phone_dic_res['factory'] = factory
        name_all = infodiv.find_all('span')[-1]
        name = name_all.string
        phone_dic_res['name'] = name
        phone_price_all = soup.select('dd[class=fc-red]')[0]
        price = phone_price_all.a.text
        phone_dic_res['price'] = price
        print(f'factory:{factory}, name:{name}, price:{price}')
        return phone_dic_res

    def get_phone_info(self):
        errorcount = 0
        proxy = self.get_proxy()
        csvfile = open('phoneinfo.csv', 'w', newline='', encoding='GBK')
        fieldnames = ['factory', 'name', 'price']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        start_url = 'https://product.pconline.com.cn/mobile/'
        response = requests.get(start_url, headers=self._get_headers(), proxies={"http": "http://{}".format(proxy)})
        res_text = response.text
        soup = BeautifulSoup(res_text, 'lxml')
        all_phoneinfo = soup.select('ul[id=JlistItems]')[0]
        all_li = all_phoneinfo.find_all('li', attrs={'class': 'item'})
        re_nextpage = re.compile('<a target="_self" class="page-next" href="(.+?)" onclick="" rel="nofollow">下一页</a>')
        for li_one in all_li:
            try:
                onephoneinfo = li_one.select('div[class=item-pic]')[0]
                phoneinfo_url = 'https:' + onephoneinfo.a['href']
                phone_res = self.get_phone_dic(phoneinfo_url)
                writer.writerow(phone_res)
                time.sleep(random.randint(2, 5))
            except:
                errorcount += 1
                if errorcount >= 2:
                    self.delete_proxy(proxy)
                    proxy = self.get_proxy()
                    errorcount = 0
                continue
        while True:
            nextpage = re_nextpage.search(res_text)
            self.delete_proxy(proxy)
            proxy = self.get_proxy()
            if nextpage:
                try:
                    next_url = 'https://product.pconline.com.cn' + nextpage.group(1)
                    print(f'Got nextpage:\n{next_url}')
                    response = requests.get(next_url, headers=self._get_headers(),
                                            proxies={"http": "http://{}".format(proxy)})
                    res_text = response.text
                    soup = BeautifulSoup(res_text, 'lxml')
                    all_phoneinfo = soup.select('ul[id=JlistItems]')[0]
                    all_li = all_phoneinfo.find_all('li', attrs={'class': 'item'})
                    for li_one in all_li:
                        try:
                            onephoneinfo = li_one.select('div[class=item-pic]')[0]
                            phoneinfo_url = 'https:' + onephoneinfo.a['href']
                            phone_res = self.get_phone_dic(phoneinfo_url)
                            writer.writerow(phone_res)
                            time.sleep(random.randint(2, 5))
                        except:
                            errorcount += 1
                            if errorcount >= 2:
                                self.delete_proxy(proxy)
                                proxy = self.get_proxy()
                                errorcount = 0
                            continue
                except:
                    continue
                time.sleep(random.randint(5, 10))
            else:
                break


if __name__ == '__main__':
    pp = PhonePrice()
    pp.get_phone_info()
    # pp.get_phone_dic()
