"""
获取ip138的信息，并且调用有道的接口翻译文本
"""
import requests
from bs4 import BeautifulSoup
import hashlib
import json

# from prepareforwork.someusefuldict import MONGO


startUrl = 'http://www.ip138.com/yuming/'

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36"
}

onetoone = {}
onetomore = {}


# 有道翻译
def trans(strword):
    transurl = 'http://openapi.youdao.com/api'
    q = strword
    froml = 'EN'
    tol = 'zh-CHS'
    # tol = 'EN'
    appKey = '4f894c1343f1f594'
    salt = '7'
    key = 'VF3AJLNUY28LGdMyEclG2HDqBo991htK'
    str = (appKey+q+salt+key).encode(encoding='UTF-8')
    md5 = hashlib.md5(str)
    sign = md5.hexdigest()
    allurlinfo = transurl+'?'+'q='+q+'&from='+froml+'&to='+tol+'&appKey='+appKey+'&salt='+salt+'&sign='+sign
    data = requests.get(allurlinfo)
    jsondata = json.loads(data.text)
    # return jsondata['translation'][0]
    return jsondata


def getinfo():
    starthtml = requests.get(startUrl, headers=headers)
    starthtml.encoding = 'utf-8'
    Soup = BeautifulSoup(starthtml.text, 'lxml')
    panels = Soup.find('div', class_='panels')
    allpanel = panels.find_all('div', class_='panel')
    return allpanel


def proces1(div):
    alltrs = div[0].find('tbody').find_all('tr')
    for tr in alltrs:
        tds = tr.find_all('td')
        key = tds[0].get_text()
        value = tds[1].get_text()
        transvalue = trans(value)
        allvalue = [transvalue, value]
        onetoone[key] = allvalue
    return


def process2(div):
    alltrs = div[1].find('tbody').find_all('tr')
    for tr in alltrs:
        tds = tr.find_all('td')
        key = tds[0].get_text()
        value = tds[1].get_text()
        transvalue = trans(value)
        allvalue = [transvalue, value]
        onetoone[key] = allvalue
    return


def process3(div):
        alltrs = div[2].find('tbody').find_all('tr')
        for tr in alltrs:
            tds = tr.find_all('td')
            if len(tds) == 1:
                value = tds[0].get_text().strip()
                if value == '其他分类':
                    break
                tranvalue = trans(value)
                allvalue = [tranvalue, value]
                continue
            else:
                for td in tds:
                    str = td.get_text()
                    res = str.strip()
                    key = res.split('.')
                    if len(key) == 1:
                        continue
                    onetoone[key[1]] = allvalue
        return


def storagedomainname():
    jsondata = json.dumps(onetoone)
    with open('domainname.json', 'a') as fp:
        fp.write(jsondata)
        print('write success!')
    inser = MONGO('localhost', 27017)
    inser.insertintomongo(onetoone)


if __name__ == '__main__':
    # soup = getinfo()
    # proces1(soup)
    # process2(soup)
    # process3(soup)
    # storagedomainname()
    a = trans('Trenton (Cadwalader & Hillcrest)')
    print(a)
